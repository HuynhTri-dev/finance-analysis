#!/usr/bin/env python3
"""
Query Explainer / Execution Plan Analyzer
Usage:
  python3 query_explainer.py explain_output.txt
  cat explain_output.txt | python3 query_explainer.py

Analyzes EXPLAIN ANALYZE output and translates complex database operations
into actionable, human-readable recommendations.
"""

import sys
import re
import argparse
from typing import List

def analyze_plan(lines: List[str]):
    print("=" * 60)
    print("🧠 QUERY EXPLAINER & OPTIMIZER")
    print("=" * 60)
    
    if not lines:
        print("No execution plan provided.")
        return
        
    full_text = "\n".join(lines)
    
    warnings = []
    insights = []
    
    # 1. Detect Seq Scan (Full Table Scan)
    seq_scans = re.findall(r'Seq Scan on (\w+)', full_text)
    if seq_scans:
        for table in set(seq_scans):
            warnings.append(f"🚩 Seq Scan (Full Table Scan) detected on table '{table}'. "
                            f"\n   ↳ This means the database is reading every single row. "
                            f"\n   ↳ FIX: Add an index on the columns used in the WHERE or JOIN clauses for '{table}'.")

    # 2. Detect Nested Loops
    if "Nested Loop" in full_text:
        insights.append("🐌 Nested Loop Join detected."
                        "\n   ↳ Nested loops are fine for small result sets, but very slow for large data."
                        "\n   ↳ FIX: If this query is slow, ensure you have indexes on the JOIN conditions to speed up the inner loop, or consider increasing work_mem to allow Hash Joins.")

    # 3. Detect Hash Joins
    if "Hash Join" in full_text:
        insights.append("⚡ Hash Join detected."
                        "\n   ↳ Good for joining large datasets, assuming enough memory is available.")

    # 4. Check for massive discrepancies between estimated rows and actual rows
    # Pattern: rows=estimated actual time=... rows=actual
    row_discrepancies = re.findall(r'rows=(\d+).*?actual time=.*?rows=(\d+)', full_text)
    for est_rows, act_rows in row_discrepancies:
        est = int(est_rows)
        act = int(act_rows)
        if est > 0 and act > 0:
            ratio = max(est/act, act/est)
            if ratio > 10:
                warnings.append(f"🚩 Bad Statistics: Estimated rows ({est}) differs heavily from Actual rows ({act})."
                                f"\n   ↳ The query planner might choose a bad plan because its statistics are outdated."
                                f"\n   ↳ FIX: Run `ANALYZE table_name;` to update statistics.")
                break # Only warn once to avoid noise

    # 5. Detect high execution time (if overall time is available)
    exec_time = re.search(r'Execution Time:\s*([0-9.]+)\s*ms', full_text, re.IGNORECASE)
    if exec_time:
        time_ms = float(exec_time.group(1))
        print(f"⏱️ Total Execution Time: {time_ms} ms")
        if time_ms > 1000:
            warnings.append("🚩 Query takes over 1 second. This is generally too slow for OLTP operations.")

    print("\n--- 🔍 ANALYSIS RESULTS ---")
    if not warnings and not insights:
        print("✅ The query plan looks optimal. No major red flags detected.")
    
    if warnings:
        print("\n🚨 CRITICAL WARNINGS:")
        for w in warnings:
            print(f"- {w}")
            
    if insights:
        print("\n💡 OPTIMIZATION INSIGHTS:")
        for i in insights:
            print(f"- {i}")

def main():
    parser = argparse.ArgumentParser(description="Analyze EXPLAIN ANALYZE output.")
    parser.add_argument("file", nargs="?", help="Path to explain log file. If omitted, reads from stdin.")
    args = parser.parse_args()

    lines = []
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
    else:
        # Read from stdin
        if not sys.stdin.isatty():
            lines = sys.stdin.readlines()
        else:
            print("Please provide a file or pipe data to stdin.")
            sys.exit(1)

    analyze_plan(lines)

if __name__ == "__main__":
    main()
