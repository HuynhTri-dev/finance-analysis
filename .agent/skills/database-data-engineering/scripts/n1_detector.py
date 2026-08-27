#!/usr/bin/env python3
"""
N+1 Query Detector
Usage: 
  python3 n1_detector.py query_log.txt
  cat query_log.txt | python3 n1_detector.py

This script reads a stream of SQL queries (one per line or from a log file),
normalizes them by replacing literals (strings, numbers) with placeholders (?),
and aggregates them to detect N+1 query patterns.
"""

import sys
import re
import argparse
from collections import Counter
from typing import List

# Threshold for N+1 warning
N1_THRESHOLD = 5

def normalize_query(query: str) -> str:
    """
    Normalizes a SQL query by replacing literals with '?'
    so that identical queries with different parameters group together.
    """
    # Convert to uppercase for consistency
    q = query.upper().strip()
    
    # Remove extra whitespaces
    q = re.sub(r'\s+', ' ', q)
    
    # Replace single-quoted strings with '?'
    q = re.sub(r"'(?:[^']|'')*'", '?', q)
    
    # Replace double-quoted strings with '?' (optional in some dialects, but safe for normalization)
    q = re.sub(r'"(?:[^"]|"")*"', '?', q)
    
    # Replace numbers with '?'
    # Handles integers and decimals like 123, 45.67, -89
    q = re.sub(r'\b-?\d+(?:\.\d+)?\b', '?', q)
    
    # Standardize IN clauses IN (?, ?, ?) -> IN (?)
    q = re.sub(r'IN\s*\(\s*(?:\?\s*,\s*)+\?\s*\)', 'IN (?)', q)
    
    return q

def detect_n1(queries: List[str]):
    print("=" * 60)
    print("🔍 N+1 QUERY DETECTOR RESULTS")
    print("=" * 60)
    
    if not queries:
        print("No queries provided.")
        return

    normalized_queries = [normalize_query(q) for q in queries if q.strip()]
    counter = Counter(normalized_queries)
    
    found_issues = False
    
    # Sort by frequency descending
    for query, count in counter.most_common():
        if count >= N1_THRESHOLD:
            found_issues = True
            print(f"\n🚨 [POTENTIAL N+1 DETECTED] Frequency: {count} times")
            print(f"Query Pattern: {query}")
            print(f"Suggestion: Consider using Eager Loading (JOIN) or Batch Fetching (WHERE id IN (...)).")
            
    if not found_issues:
        print("\n✅ No obvious N+1 patterns detected (Threshold: {} occurrences).".format(N1_THRESHOLD))
        
    print("\nTotal unique query patterns analyzed: ", len(counter))
    print("Total queries processed: ", len(normalized_queries))

def main():
    global N1_THRESHOLD
    parser = argparse.ArgumentParser(description="Detect N+1 queries from SQL logs.")
    parser.add_argument("file", nargs="?", help="Path to SQL log file. If omitted, reads from stdin.")
    parser.add_argument("--threshold", type=int, default=N1_THRESHOLD, help="Minimum occurrences to trigger warning (default: 5)")
    args = parser.parse_args()

    N1_THRESHOLD = args.threshold

    queries = []
    
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                queries = f.readlines()
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
    else:
        # Read from stdin
        if not sys.stdin.isatty():
            queries = sys.stdin.readlines()
        else:
            print("Please provide a file or pipe data to stdin.")
            sys.exit(1)

    detect_n1(queries)

if __name__ == "__main__":
    main()
