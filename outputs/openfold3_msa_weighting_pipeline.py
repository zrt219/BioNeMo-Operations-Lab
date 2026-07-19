#!/usr/bin/env python3
"""OpenFold3 MSA weighting pipeline.

This script treats each homolog row as a weighted branch in a deterministic
but probabilistic scoring graph:

    support = a*identity + b*coverage + c*motif + d*column_information
              + e*novelty + f*lineage_centrality - g*gaps
    weight  = softmax(support / temperature)

The terms are deterministic heuristics, not a biological evolutionary model.
They make the demonstration less sensitive to input row order and preserve
diverse representatives when a caller asks for a reduced alignment.

It then emits:
- a weighted A3M file
- a weighted paired-MSA CSV file
- branch-score JSON
- consensus JSON
- an OpenFold3 request JSON payload

The paired-MSA handling is intentionally schema-conservative: the CSV is passed
through as a text block and reordered by branch weight, but no unsupported fields
are invented.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


AA_ALPHABET = set("ACDEFGHIKLMNPQRSTVWY-")
DEFAULT_QUERY = "MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIE"
HOSTED_OPENFOLD3_URL = "https://health.api.nvidia.com/v1/biology/openfold/openfold3/predict"


@dataclass
class AlignmentRow:
    header: str
    sequence: str


@dataclass
class RowScore:
    header: str
    sequence: str
    identity: float
    coverage: float
    gap_fraction: float
    motif_score: float
    redundancy: float
    neighbor_count: int
    novelty: float
    column_information: float
    lineage_centrality: float
    support: float
    weight: float = 0.0


def clean_sequence(raw: str) -> str:
    seq = "".join(raw.split()).upper()
    invalid = sorted(set(seq) - AA_ALPHABET)
    if invalid:
        raise ValueError(f"Unsupported alignment characters: {''.join(invalid)}")
    return seq


def parse_a3m(path: Path) -> tuple[str, list[AlignmentRow]]:
    records: list[AlignmentRow] = []
    current_header: str | None = None
    chunks: list[str] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if current_header is not None:
                records.append(AlignmentRow(current_header, clean_sequence("".join(chunks))))
            current_header = line[1:].strip()
            chunks = []
        else:
            chunks.append(line)

    if current_header is not None:
        records.append(AlignmentRow(current_header, clean_sequence("".join(chunks))))

    if not records:
        raise ValueError(f"No FASTA records found in {path}")

    query = records[0].sequence
    for row in records[1:]:
        if len(row.sequence) != len(query):
            raise ValueError(
                f"A3M row {row.header!r} has length {len(row.sequence)}; expected {len(query)}"
            )
    return query, records[1:]


def parse_paired_csv(path: Path, query_len: int) -> list[AlignmentRow]:
    rows: list[AlignmentRow] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path} is missing a CSV header")
        required = {"key", "sequence"}
        if not required.issubset(set(reader.fieldnames)):
            raise ValueError(f"{path} must contain the columns: key,sequence")

        for index, raw in enumerate(reader, start=1):
            key = (raw.get("key") or "").strip()
            sequence = clean_sequence(raw.get("sequence") or "")
            if len(sequence) != query_len:
                raise ValueError(
                    f"Paired CSV row {index} has length {len(sequence)}; expected {query_len}"
                )
            rows.append(AlignmentRow(key or f"pair_{index:02d}", sequence))

    if not rows:
        raise ValueError(f"No paired-MSA rows found in {path}")
    return rows


def pairwise_identity(a: str, b: str) -> float:
    matches = 0
    aligned = 0
    for left, right in zip(a, b):
        if left == "-" or right == "-":
            continue
        aligned += 1
        if left == right:
            matches += 1
    return matches / aligned if aligned else 0.0


def max_match_run(query: str, seq: str) -> int:
    best = 0
    run = 0
    for q, s in zip(query, seq):
        if q != "-" and s != "-" and q == s:
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best


def column_information_profile(query: str, rows: Sequence[AlignmentRow]) -> list[float]:
    """Return normalized conservation for each query-aligned column."""
    profile: list[float] = []
    all_sequences = [query, *(row.sequence for row in rows)]
    for index in range(len(query)):
        counts: dict[str, int] = {}
        for sequence in all_sequences:
            residue = sequence[index]
            if residue != "-":
                counts[residue] = counts.get(residue, 0) + 1
        total = sum(counts.values())
        if total <= 1:
            profile.append(0.0)
            continue
        entropy = -sum(
            (count / total) * math.log(count / total, 2) for count in counts.values()
        )
        max_entropy = math.log(min(len(counts), 20), 2) if len(counts) > 1 else 0.0
        profile.append(1.0 - entropy / max_entropy if max_entropy else 1.0)
    return profile


def lineage_centralities(rows: Sequence[AlignmentRow], kernel_scale: float = 0.12) -> list[float]:
    """Score how consistently each row connects to the non-identical family."""
    if not rows:
        return []
    raw: list[float] = []
    for row in rows:
        affinities = []
        for peer in rows:
            if peer is row:
                continue
            distance = 1.0 - pairwise_identity(row.sequence, peer.sequence)
            affinities.append(math.exp(-(distance * distance) / (2.0 * kernel_scale**2)))
        raw.append(sum(affinities) / len(affinities) if affinities else 0.0)
    maximum = max(raw)
    return [value / maximum if maximum else 0.0 for value in raw]


def score_rows(
    query: str,
    rows: Sequence[AlignmentRow],
    temperature: float,
    neighbor_identity: float,
) -> list[RowScore]:
    information = column_information_profile(query, rows)
    centralities = lineage_centralities(rows)
    scored: list[RowScore] = []
    for row_index, row in enumerate(rows):
        identity = pairwise_identity(query, row.sequence)
        coverage = sum(1 for ch in row.sequence if ch != "-") / len(query)
        gap_fraction = row.sequence.count("-") / len(query)
        motif_score = max_match_run(query, row.sequence) / len(query)
        peer_identities = [
            pairwise_identity(row.sequence, peer.sequence)
            for peer_index, peer in enumerate(rows)
            if peer_index != row_index
        ]
        redundancy = max(peer_identities, default=0.0)
        neighbor_count = sum(value >= neighbor_identity for value in peer_identities)
        novelty = 1.0 / (1.0 + neighbor_count)
        matched_information = [
            information[index]
            for index, (query_residue, residue) in enumerate(zip(query, row.sequence))
            if residue != "-" and residue == query_residue
        ]
        column_info = sum(matched_information) / len(query) if matched_information else 0.0
        lineage_centrality = centralities[row_index]

        support = (
            1.75 * identity
            + 0.90 * coverage
            + 0.40 * motif_score
            + 0.65 * column_info
            + 0.70 * novelty
            + 0.35 * lineage_centrality
            - 0.95 * gap_fraction
        )
        scored.append(
            RowScore(
                header=row.header,
                sequence=row.sequence,
                identity=identity,
                coverage=coverage,
                gap_fraction=gap_fraction,
                motif_score=motif_score,
                redundancy=redundancy,
                neighbor_count=neighbor_count,
                novelty=novelty,
                column_information=column_info,
                lineage_centrality=lineage_centrality,
                support=support,
            )
        )

    if not scored:
        return []

    max_support = max(item.support for item in scored)
    numerators = [math.exp((item.support - max_support) / temperature) for item in scored]
    denominator = sum(numerators)
    for item, numerator in zip(scored, numerators):
        item.weight = numerator / denominator if denominator else 0.0
    return scored


def select_diverse_rows(
    rows: Sequence[RowScore], max_rows: int, diversity_strength: float,
) -> list[RowScore]:
    """Select high-support rows while penalizing near-duplicate representatives."""
    if max_rows < 1:
        raise ValueError("max_rows must be at least 1")
    candidates = sorted(rows, key=lambda row: (-row.weight, row.header, row.sequence))
    selected: list[RowScore] = []
    while candidates and len(selected) < max_rows:
        def marginal_score(candidate: RowScore) -> tuple[float, float, str]:
            similarity = max(
                (pairwise_identity(candidate.sequence, picked.sequence) for picked in selected),
                default=0.0,
            )
            return (candidate.support - diversity_strength * similarity, candidate.weight, candidate.header)

        best = max(candidates, key=marginal_score)
        selected.append(best)
        candidates.remove(best)
    return selected


def weighted_consensus(query: str, rows: Sequence[RowScore], query_prior: float = 0.85) -> dict:
    columns = []
    for index, query_residue in enumerate(query):
        counts: dict[str, float] = {}
        if query_residue != "-":
            counts[query_residue] = query_prior
        for row in rows:
            residue = row.sequence[index]
            if residue == "-":
                continue
            counts[residue] = counts.get(residue, 0.0) + row.weight

        if not counts:
            columns.append(
                {
                    "index": index + 1,
                    "consensus": "-",
                    "confidence": 0.0,
                    "entropy": 0.0,
                }
            )
            continue

        total = sum(counts.values())
        consensus_residue, consensus_count = max(counts.items(), key=lambda item: item[1])
        probs = [value / total for value in counts.values()]
        entropy = -sum(p * math.log(p, 2) for p in probs if p > 0)
        columns.append(
            {
                "index": index + 1,
                "consensus": consensus_residue,
                "confidence": consensus_count / total,
                "entropy": entropy,
            }
        )

    return {
        "consensus_sequence": "".join(column["consensus"] for column in columns),
        "columns": columns,
        "query_prior": query_prior,
    }


def render_a3m(query: str, rows: Sequence[RowScore]) -> str:
    lines = [">query", query]
    for index, row in enumerate(sorted(rows, key=lambda item: item.weight, reverse=True), start=1):
        lines.append(
            f">{row.header}|rank={index:02d}|w={row.weight:.4f}|id={row.identity:.3f}|cov={row.coverage:.3f}"
        )
        lines.append(row.sequence)
    return "\n".join(lines) + "\n"


def render_paired_csv(rows: Sequence[RowScore]) -> str:
    output = ["key,sequence"]
    for row in sorted(rows, key=lambda item: item.weight, reverse=True):
        output.append(f"{row.header},{row.sequence}")
    return "\n".join(output) + "\n"


def build_openfold3_payload(
    query: str,
    msa_text: str,
    output_format: str,
    input_id: str,
    paired_text: str | None = None,
) -> dict:
    molecule: dict[str, object] = {
        "type": "protein",
        "id": "A",
        "sequence": query,
        "msa": {
            "main": {
                "a3m": {
                    "alignment": msa_text,
                    "format": "a3m",
                }
            }
        },
    }
    if paired_text is not None:
        molecule["paired_msa"] = {
            "main": {
                "csv": {
                    "alignment": paired_text,
                    "format": "csv",
                }
            }
        }

    return {
        "inputs": [
            {
                "input_id": input_id,
                "output_format": output_format,
                "molecules": [molecule],
            }
        ]
    }


def submit_openfold3(payload: dict, api_key_env: str) -> dict:
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise RuntimeError(f"{api_key_env} is required for hosted submission")

    request = urllib.request.Request(
        HOSTED_OPENFOLD3_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenFold3 request failed: {exc.code} {body}") from exc


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_next_run_command(path: Path, next_defaults: dict, args: argparse.Namespace) -> None:
    command = [
        "python",
        "outputs\\openfold3_msa_weighting_pipeline.py",
        "--msa",
        str(args.msa),
        "--paired",
        str(args.paired),
        "--output-dir",
        str(args.output_dir),
        "--feedback-state",
        str(args.feedback_state),
        "--run-registry",
        str(args.run_registry),
        "--seed-comparison",
        str(args.seed_comparison),
        "--summary",
        str(args.summary),
        "--temperature",
        str(next_defaults["temperature"]),
        "--diversity-strength",
        str(next_defaults["diversity_strength"]),
        "--neighbor-identity",
        str(next_defaults["neighbor_identity"]),
    ]
    path.write_text(
        "\n".join(
            [
                "# MOCK / DEMO recommended next run",
                " ".join(command),
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_next_run_rationale(path: Path, comparison_report: dict) -> None:
    rationale_lines = [
        "# MOCK / DEMO next-run rationale",
        f"rule: {comparison_report['next_heuristic_defaults']['rule']}",
        f"latest_vs_previous_msa_neff_delta: {comparison_report['latest_vs_previous']['msa_neff_delta']}",
        f"latest_vs_previous_paired_neff_delta: {comparison_report['latest_vs_previous']['paired_neff_delta']}",
        f"latest_vs_best_msa_neff_delta: {comparison_report['latest_vs_best']['msa_neff_delta']}",
        f"latest_vs_best_paired_neff_delta: {comparison_report['latest_vs_best']['paired_neff_delta']}",
        "interpretation: " + comparison_report["interpretation"],
        "",
    ]
    path.write_text("\n".join(rationale_lines), encoding="utf-8")


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_heuristic_defaults(
    args: argparse.Namespace,
    seed_comparison_path: Path,
) -> tuple[float, float, float, dict]:
    """Resolve the next run's heuristic defaults from history unless overridden."""
    seed_report = load_json(seed_comparison_path)
    recommended = seed_report.get("next_heuristic_defaults", {})

    temperature = args.temperature if args.temperature is not None else recommended.get("temperature", 0.35)
    neighbor_identity = (
        args.neighbor_identity if args.neighbor_identity is not None else recommended.get("neighbor_identity", 0.95)
    )
    diversity_strength = (
        args.diversity_strength if args.diversity_strength is not None else recommended.get("diversity_strength", 0.45)
    )
    return temperature, neighbor_identity, diversity_strength, recommended


def clipped_weight(current: float, previous: float, current_weight: float, previous_weight: float, lower: float, upper: float) -> float:
    blended = (previous * previous_weight) + (current * current_weight)
    return round(max(lower, min(upper, blended)), 4)


def compute_run_deltas(current_entry: dict, previous: dict | None) -> dict:
    if not previous:
        return {
            "msa_neff_delta": current_entry["msa_neff"],
            "paired_neff_delta": current_entry["paired_neff"],
            "temperature_delta": current_entry["temperature"],
            "diversity_strength_delta": current_entry["diversity_strength"],
            "neighbor_identity_delta": current_entry["neighbor_identity"],
        }
    return {
        "msa_neff_delta": current_entry["msa_neff"] - previous.get("msa_neff", 0.0),
        "paired_neff_delta": current_entry["paired_neff"] - previous.get("paired_neff", 0.0),
        "temperature_delta": current_entry["temperature"] - previous.get("temperature", 0.0),
        "diversity_strength_delta": current_entry["diversity_strength"] - previous.get("diversity_strength", 0.0),
        "neighbor_identity_delta": current_entry["neighbor_identity"] - previous.get("neighbor_identity", 0.0),
    }


def build_registry_entry(
    branch_scores: dict,
    msa_consensus: dict,
    paired_consensus: dict,
    args: argparse.Namespace,
    run_index: int,
) -> dict:
    return {
        "run_index": run_index,
        "query": branch_scores["query"],
        "temperature": branch_scores["temperature"],
        "neighbor_identity": branch_scores["neighbor_identity"],
        "diversity_strength": branch_scores["diversity_strength"],
        "msa_neff": branch_scores["msa_neff"],
        "paired_neff": branch_scores["paired_neff"],
        "msa_top_header": branch_scores["selected_msa_headers"][0] if branch_scores["selected_msa_headers"] else None,
        "paired_top_key": branch_scores["selected_paired_keys"][0] if branch_scores["selected_paired_keys"] else None,
        "msa_consensus": msa_consensus["consensus_sequence"],
        "paired_consensus": paired_consensus["consensus_sequence"],
        "heuristic_update_rule": {
            "temperature": "average(current, previous)",
            "diversity_strength": "0.7*previous + 0.3*current, clipped to [0.05, 1.0]",
            "neighbor_identity": "0.8*previous + 0.2*current, clipped to [0.5, 0.99]",
        },
        "requested_defaults": {
            "temperature": args.temperature,
            "neighbor_identity": args.neighbor_identity,
            "diversity_strength": args.diversity_strength,
        },
    }


def _calculate_deltas(latest: dict, comparison: dict) -> dict:
    def diff(field: str) -> float:
        return round(latest.get(field, 0.0) - comparison.get(field, 0.0), 6)

    return {
        "temperature_delta": diff("temperature"),
        "neighbor_identity_delta": diff("neighbor_identity"),
        "diversity_strength_delta": diff("diversity_strength"),
        "msa_neff_delta": diff("msa_neff"),
        "paired_neff_delta": diff("paired_neff"),
    }


def _calculate_next_defaults(latest_run: dict, best_run: dict, latest_vs_previous: dict) -> dict:
    current_temp = latest_run.get("temperature", 0.35)
    current_neighbor = latest_run.get("neighbor_identity", 0.95)
    current_diversity = latest_run.get("diversity_strength", 0.45)
    msa_delta = latest_vs_previous.get("msa_neff_delta", 0.0)
    paired_delta = latest_vs_previous.get("paired_neff_delta", 0.0)
    strength_signal = msa_delta + paired_delta

    if strength_signal > 0:
        return {
            "temperature": round(max(0.15, current_temp * 0.95), 4),
            "neighbor_identity": round(min(0.99, current_neighbor + 0.01), 4),
            "diversity_strength": round(max(0.05, current_diversity * 0.9), 4),
            "rule": "exploit-neff",
        }
    if strength_signal < 0:
        return {
            "temperature": round(min(0.8, current_temp * 1.05), 4),
            "neighbor_identity": round(max(0.5, current_neighbor - 0.01), 4),
            "diversity_strength": round(min(1.0, current_diversity * 1.1), 4),
            "rule": "expand-diversity",
        }
    return {
        "temperature": round(max(0.15, min(0.8, (current_temp + best_run.get("temperature", current_temp)) / 2.0)), 4),
        "neighbor_identity": round(max(0.5, min(0.99, (current_neighbor + best_run.get("neighbor_identity", current_neighbor)) / 2.0)), 4),
        "diversity_strength": round(max(0.05, min(1.0, (current_diversity + best_run.get("diversity_strength", current_diversity)) / 2.0)), 4),
        "rule": "blend-best-and-latest",
    }


def build_comparison_report(
    latest_run: dict,
    previous_run: dict | None,
    best_run: dict | None,
) -> dict:
    """Create a human-readable local comparison record."""
    if previous_run is None:
        previous_run = latest_run
    if best_run is None:
        best_run = latest_run

    latest_vs_previous = _calculate_deltas(latest_run, previous_run)
    latest_vs_previous["msa_top_header"] = latest_run.get("msa_top_header")
    latest_vs_previous["paired_top_key"] = latest_run.get("paired_top_key")

    latest_vs_best = _calculate_deltas(latest_run, best_run)

    report = {
        "status": "MOCK / DEMO",
        "run_index": latest_run.get("run_index"),
        "query": latest_run.get("query"),
        "latest_vs_previous": latest_vs_previous,
        "latest_vs_best": latest_vs_best,
        "best_run": {
            "run_index": best_run.get("run_index"),
            "msa_neff": best_run.get("msa_neff"),
            "paired_neff": best_run.get("paired_neff"),
            "msa_top_header": best_run.get("msa_top_header"),
            "paired_top_key": best_run.get("paired_top_key"),
        },
        "next_heuristic_defaults": _calculate_next_defaults(latest_run, best_run, latest_vs_previous),
        "heuristic_update_rule": latest_run.get("heuristic_update_rule", {}),
        "interpretation": (
            "Positive neff deltas suggest broader local support; negative deltas suggest "
            "the current input narrowed the effective family. This is a deterministic demo "
            "comparison, not a biological truth claim."
        ),
    }
    return report


def update_feedback_state(
    state: dict,
    branch_scores: dict,
    msa_consensus: dict,
    paired_consensus: dict,
    args: argparse.Namespace,
) -> dict:
    """Update deterministic heuristic state from the current run."""
    previous_runs = state.get("runs", [])
    run_index = len(previous_runs) + 1
    current_entry = build_registry_entry(branch_scores, msa_consensus, paired_consensus, args, run_index)

    previous = previous_runs[-1] if previous_runs else None
    current_entry["deltas"] = compute_run_deltas(current_entry, previous)

    state.setdefault("runs", []).append(current_entry)
    state["latest_run"] = current_entry
    if previous:
        state["heuristic_defaults"] = {
            "temperature": round((previous.get("temperature", args.temperature) + args.temperature) / 2.0, 4),
            "diversity_strength": clipped_weight(
                args.diversity_strength,
                previous.get("diversity_strength", args.diversity_strength),
                0.3,
                0.7,
                0.05,
                1.0,
            ),
            "neighbor_identity": clipped_weight(
                args.neighbor_identity,
                previous.get("neighbor_identity", args.neighbor_identity),
                0.2,
                0.8,
                0.5,
                0.99,
            ),
        }
    else:
        state["heuristic_defaults"] = {
            "temperature": args.temperature,
            "neighbor_identity": args.neighbor_identity,
            "diversity_strength": args.diversity_strength,
        }

    state["version"] = 1
    return state


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score and weight OpenFold3 MSAs.")
    parser.add_argument("--msa", type=Path, default=Path("openfold3_msa_mock.a3m"))
    parser.add_argument("--paired", type=Path, default=Path("openfold3_paired_msa_mock.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--max-rows", type=int, default=12)
    parser.add_argument(
        "--neighbor-identity",
        type=float,
        default=None,
        help="Identity threshold used to define a local sequence neighborhood.",
    )
    parser.add_argument(
        "--diversity-strength",
        type=float,
        default=None,
        help="Max-marginal-relevance penalty for selected near-duplicates.",
    )
    parser.add_argument("--output-format", choices=("pdb", "cif"), default="pdb")
    parser.add_argument("--input-id", default="openfold3_weighted_demo")
    parser.add_argument("--request-id", default="openfold3-weighted-pack")
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--api-key-env", default="NGC_API_KEY")
    parser.add_argument("--feedback-state", type=Path, default=Path("openfold3_feedback_state.json"))
    parser.add_argument("--run-registry", type=Path, default=Path("openfold3_run_registry.json"))
    parser.add_argument("--seed-comparison", type=Path, default=Path("openfold3_run_comparison.json"))
    parser.add_argument("--summary", type=Path, default=Path("openfold3_run_summary.json"))
    args = parser.parse_args(argv)

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    query, msa_rows_raw = parse_a3m(args.msa)
    paired_rows_raw = parse_paired_csv(args.paired, len(query))

    temperature, neighbor_identity, diversity_strength, seeded_defaults = resolve_heuristic_defaults(args, args.seed_comparison)

    if not 0.0 < temperature:
        raise ValueError("temperature must be greater than 0")
    if not 0.0 <= neighbor_identity <= 1.0:
        raise ValueError("neighbor-identity must be between 0 and 1")
    if diversity_strength < 0.0:
        raise ValueError("diversity-strength must be non-negative")

    msa_scored = score_rows(query, msa_rows_raw, temperature, neighbor_identity)
    paired_scored = score_rows(query, paired_rows_raw, temperature, neighbor_identity)
    selected_msa = select_diverse_rows(msa_scored, args.max_rows, diversity_strength)
    selected_paired = select_diverse_rows(paired_scored, args.max_rows, diversity_strength)

    msa_consensus = weighted_consensus(query, msa_scored)
    paired_consensus = weighted_consensus(query, paired_scored)

    weighted_msa_text = render_a3m(query, selected_msa)
    weighted_paired_csv_text = render_paired_csv(selected_paired)

    weighted_msa_path = output_dir / "openfold3_weighted_msa.a3m"
    weighted_paired_path = output_dir / "openfold3_weighted_paired_msa.csv"
    scores_path = output_dir / "openfold3_branch_scores.json"
    consensus_path = output_dir / "openfold3_consensus.json"
    diagnostics_path = output_dir / "openfold3_alignment_diagnostics.json"
    request_path = output_dir / "openfold3_weighted_request.json"

    write_text(weighted_msa_path, weighted_msa_text)
    write_text(weighted_paired_path, weighted_paired_csv_text)

    branch_scores = {
        "query": query,
        "model": "MOCK deterministic lineage-aware MSA weighting heuristic",
        "temperature": temperature,
        "neighbor_identity": neighbor_identity,
        "diversity_strength": diversity_strength,
        "msa_rows": [asdict(row) for row in sorted(msa_scored, key=lambda item: item.weight, reverse=True)],
        "paired_rows": [asdict(row) for row in sorted(paired_scored, key=lambda item: item.weight, reverse=True)],
        "selected_msa_headers": [row.header for row in selected_msa],
        "selected_paired_keys": [row.header for row in selected_paired],
        "msa_neff": 1.0 / sum(row.weight**2 for row in msa_scored) if msa_scored else 0.0,
        "paired_neff": 1.0 / sum(row.weight**2 for row in paired_scored) if paired_scored else 0.0,
    }
    write_json(scores_path, branch_scores)
    write_json(
        diagnostics_path,
        {
            "status": "MOCK / DEMO",
            "interpretation": (
                "Scores describe deterministic alignment heuristics only. They are not "
                "evolutionary distances, structure confidence, or evidence of inheritance."
            ),
            "formula": {
                "branch_support": (
                    "1.75*identity + 0.90*coverage + 0.40*motif + "
                    "0.65*column_information + 0.70*novelty + "
                    "0.35*lineage_centrality - 0.95*gap_fraction"
                ),
                "branch_weight": "softmax(branch_support / temperature)",
                "lineage_centrality": "mean(exp(-sequence_distance^2 / (2*0.12^2)))",
                "selection": "support - diversity_strength * max_similarity_to_selected",
            },
            "msa": {
                "input_rows": len(msa_scored),
                "selected_rows": len(selected_msa),
                "effective_sequence_count": branch_scores["msa_neff"],
                "mean_column_information": sum(column_information_profile(query, msa_rows_raw)) / len(query),
            },
            "paired_msa": {
                "input_rows": len(paired_scored),
                "selected_rows": len(selected_paired),
                "effective_sequence_count": branch_scores["paired_neff"],
                "mean_column_information": sum(column_information_profile(query, paired_rows_raw)) / len(query),
            },
        },
    )
    write_json(
        consensus_path,
        {
            "msa": msa_consensus,
            "paired_msa": paired_consensus,
            "note": "Demo consensus derived from weighted branch support, not a real homolog search.",
        },
    )

    payload = build_openfold3_payload(
        query=query,
        msa_text=weighted_msa_text,
        output_format=args.output_format,
        input_id=args.input_id,
        paired_text=weighted_paired_csv_text,
    )
    payload["request_id"] = args.request_id
    write_json(request_path, payload)

    feedback_state = load_json(args.feedback_state)
    feedback_state = update_feedback_state(
        feedback_state,
        branch_scores,
        msa_consensus,
        paired_consensus,
        argparse.Namespace(
            temperature=temperature,
            neighbor_identity=neighbor_identity,
            diversity_strength=diversity_strength,
        ),
    )
    write_json(args.feedback_state, feedback_state)

    registry = load_json(args.run_registry)
    registry_runs = registry.get("runs", [])
    current_run = feedback_state["latest_run"]
    previous_run = registry_runs[-1] if registry_runs else None
    current_run["registry_deltas"] = compute_run_deltas(current_run, previous_run)
    registry_runs.append(current_run)
    registry["version"] = 1
    registry["runs"] = registry_runs
    registry["latest_run"] = current_run
    registry["best_run"] = max(registry_runs, key=lambda item: (item.get("msa_neff", 0.0), item.get("paired_neff", 0.0), -item.get("temperature", 0.0)))
    write_json(args.run_registry, registry)

    comparison_report = build_comparison_report(current_run, previous_run, registry["best_run"])
    comparison_path = output_dir / "openfold3_run_comparison.json"
    next_run_path = output_dir / "openfold3_next_run_command.txt"
    rationale_path = output_dir / "openfold3_next_run_rationale.txt"
    write_json(comparison_path, comparison_report)
    write_next_run_command(next_run_path, comparison_report["next_heuristic_defaults"], args)
    write_next_run_rationale(rationale_path, comparison_report)

    write_json(
        args.summary,
        {
            "status": "MOCK / DEMO",
            "request_id": args.request_id,
            "input_msa": str(args.msa),
            "input_paired": str(args.paired),
            "outputs": {
                "weighted_msa": str(weighted_msa_path),
                "weighted_paired_msa": str(weighted_paired_path),
                "scores": str(scores_path),
                "consensus": str(consensus_path),
                "diagnostics": str(diagnostics_path),
                "request": str(request_path),
                "feedback_state": str(args.feedback_state),
                "run_registry": str(args.run_registry),
                "comparison": str(comparison_path),
                "next_run_command": str(next_run_path),
                "next_run_rationale": str(rationale_path),
            },
            "selected_msa_headers": branch_scores["selected_msa_headers"],
            "selected_paired_keys": branch_scores["selected_paired_keys"],
            "msa_neff": branch_scores["msa_neff"],
            "paired_neff": branch_scores["paired_neff"],
            "heuristic_defaults": feedback_state["heuristic_defaults"],
            "latest_run_deltas": current_run["deltas"],
            "comparison_report": comparison_report,
            "next_heuristic_defaults": comparison_report["next_heuristic_defaults"],
            "seeded_defaults": seeded_defaults,
        },
    )

    print(f"Wrote {weighted_msa_path.name}")
    print(f"Wrote {weighted_paired_path.name}")
    print(f"Wrote {scores_path.name}")
    print(f"Wrote {consensus_path.name}")
    print(f"Wrote {diagnostics_path.name}")
    print(f"Wrote {request_path.name}")
    print(f"Wrote {args.feedback_state.name}")
    print(f"Wrote {args.run_registry.name}")
    print(f"Wrote {comparison_path.name}")
    print(f"Wrote {next_run_path.name}")
    print(f"Wrote {rationale_path.name}")
    print(f"Wrote {args.summary.name}")
    print(f"MSA consensus: {msa_consensus['consensus_sequence']}")
    print(f"Paired consensus: {paired_consensus['consensus_sequence']}")

    if args.submit:
        response = submit_openfold3(payload, args.api_key_env)
        response_path = output_dir / "openfold3_weighted_response.json"
        write_json(response_path, response)
        print(f"Wrote {response_path.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
