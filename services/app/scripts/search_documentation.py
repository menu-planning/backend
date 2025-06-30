#!/usr/bin/env python3
"""
Documentation Search Script for API Schema Patterns

Simple search functionality for finding relevant documentation sections
based on keywords, patterns, or concepts.

Usage:
    python scripts/search_documentation.py "typeadapter"
    python scripts/search_documentation.py "performance" --detailed
    python scripts/search_documentation.py "collection" --files-only
"""

import os
import re
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import json


class DocumentationSearcher:
    """Simple documentation search functionality."""
    
    def __init__(self, docs_root: Path):
        self.docs_root = docs_root
        self.api_patterns_root = docs_root / "architecture" / "api-schema-patterns"
        
        # Define documentation structure with descriptions
        self.documentation_index = {
            "overview.md": {
                "title": "API Schema Patterns Overview",
                "description": "Complete four-layer conversion pattern explanation",
                "keywords": ["four-layer", "conversion", "overview", "pattern", "domain", "api", "orm", "database"]
            },
            "migration-guide.md": {
                "title": "Migration Guide", 
                "description": "Step-by-step schema migration process",
                "keywords": ["migration", "upgrade", "existing", "assessment", "checklist", "phases"]
            },
            "patterns/type-conversions.md": {
                "title": "Type Conversion Patterns",
                "description": "Comprehensive type conversion matrix and strategies",
                "keywords": ["type", "conversion", "set", "frozenset", "list", "scalar", "collection"]
            },
            "patterns/computed-properties.md": {
                "title": "Computed Properties Patterns",
                "description": "Three-layer computed property handling",
                "keywords": ["computed", "property", "cached", "materialization", "domain", "api", "orm"]
            },
            "patterns/typeadapter-usage.md": {
                "title": "TypeAdapter Usage Patterns",
                "description": "Performance-optimized TypeAdapter implementation",
                "keywords": ["typeadapter", "singleton", "performance", "validation", "thread", "memory"]
            },
            "patterns/field-validation.md": {
                "title": "Field Validation Patterns",
                "description": "Comprehensive field validation strategies",
                "keywords": ["validation", "beforevalidator", "aftervalidator", "field_validator", "sanitization"]
            },
            "patterns/sqlalchemy-composite-integration.md": {
                "title": "SQLAlchemy Composite Integration",
                "description": "Patterns for SQLAlchemy composite fields",
                "keywords": ["sqlalchemy", "composite", "field", "orm", "integration", "database"]
            },
            "patterns/collection-handling.md": {
                "title": "Collection Handling Patterns",
                "description": "Strategies for collection order and uniqueness",
                "keywords": ["collection", "set", "frozenset", "list", "order", "uniqueness", "json"]
            },
            "examples/meal-schema-complete.md": {
                "title": "Complete ApiMeal Example",
                "description": "Field-by-field analysis of complete implementation",
                "keywords": ["example", "meal", "apimeal", "reference", "implementation", "complete"]
            }
        }
        
        # Performance benchmarks for quick reference
        self.performance_benchmarks = {
            "TypeAdapter validation": "0.02ms (50x better than target)",
            "Four-layer conversion": "~59μs (847x better than target)",
            "Field validation": "~0.2μs (5000x better than target)",
            "Composite fields": "5.6μs (1785x better than target)",
            "Collection handling": "< 3ms (target met)"
        }
        
        # Quick pattern decisions
        self.pattern_decisions = {
            "new schema": "Four-layer conversion pattern → overview.md",
            "collection": "Set → Frozenset → List → patterns/collection-handling.md",
            "computed property": "Three-layer materialization → patterns/computed-properties.md",
            "performance": "TypeAdapter singleton → patterns/typeadapter-usage.md",
            "validation": "BeforeValidator + field_validator → patterns/field-validation.md",
            "composite": "Four composite patterns → patterns/sqlalchemy-composite-integration.md",
            "migration": "Assessment + implementation → migration-guide.md",
            "example": "Complete reference implementation → examples/meal-schema-complete.md"
        }

    def search(self, query: str, detailed: bool = False, files_only: bool = False) -> Dict:
        """Search documentation for query terms."""
        query_lower = query.lower()
        results = {
            "query": query,
            "matches": [],
            "pattern_suggestions": [],
            "performance_info": [],
            "quick_links": []
        }
        
        # 1. Search documentation index
        for file_path, info in self.documentation_index.items():
            score = 0
            matched_keywords = []
            
            # Check title match
            if query_lower in info["title"].lower():
                score += 10
                
            # Check description match
            if query_lower in info["description"].lower():
                score += 5
                
            # Check keyword matches
            for keyword in info["keywords"]:
                if query_lower in keyword or keyword in query_lower:
                    score += 3
                    matched_keywords.append(keyword)
            
            if score > 0:
                match = {
                    "file": file_path,
                    "title": info["title"],
                    "description": info["description"],
                    "score": score,
                    "matched_keywords": matched_keywords,
                    "full_path": str(self.api_patterns_root / file_path)
                }
                results["matches"].append(match)
        
        # 2. Pattern decision suggestions
        for pattern_key, suggestion in self.pattern_decisions.items():
            if query_lower in pattern_key or pattern_key in query_lower:
                results["pattern_suggestions"].append({
                    "pattern": pattern_key,
                    "suggestion": suggestion
                })
        
        # 3. Performance information
        for perf_key, perf_info in self.performance_benchmarks.items():
            if query_lower in perf_key.lower():
                results["performance_info"].append({
                    "metric": perf_key,
                    "benchmark": perf_info
                })
        
        # 4. Sort matches by score
        results["matches"].sort(key=lambda x: x["score"], reverse=True)
        
        # 5. Add quick links for common queries
        if "start" in query_lower or "begin" in query_lower or "new" in query_lower:
            results["quick_links"].append("📋 Start here: overview.md")
            results["quick_links"].append("🚀 Implementation: migration-guide.md")
            results["quick_links"].append("📖 Example: examples/meal-schema-complete.md")
        
        return results

    def search_file_content(self, query: str, file_path: Path) -> List[Tuple[int, str]]:
        """Search within a specific file and return matching lines."""
        matches = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if query.lower() in line.lower():
                        matches.append((line_num, line.strip()))
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        return matches

    def format_results(self, results: Dict, detailed: bool = False, files_only: bool = False) -> str:
        """Format search results for display."""
        output = []
        query = results["query"]
        
        if files_only:
            output.append(f"📁 Files matching '{query}':\n")
            for match in results["matches"]:
                output.append(f"  • {match['file']} - {match['title']}")
            return "\n".join(output)
        
        output.append(f"🔍 Search Results for '{query}'\n")
        
        # Pattern suggestions
        if results["pattern_suggestions"]:
            output.append("🎯 Pattern Suggestions:")
            for suggestion in results["pattern_suggestions"]:
                output.append(f"  • {suggestion['pattern']}: {suggestion['suggestion']}")
            output.append("")
        
        # Quick links
        if results["quick_links"]:
            output.append("🚀 Quick Links:")
            for link in results["quick_links"]:
                output.append(f"  • {link}")
            output.append("")
        
        # Performance info
        if results["performance_info"]:
            output.append("⚡ Performance Information:")
            for perf in results["performance_info"]:
                output.append(f"  • {perf['metric']}: {perf['benchmark']}")
            output.append("")
        
        # Documentation matches
        if results["matches"]:
            output.append("📚 Documentation Matches:")
            for match in results["matches"][:5]:  # Show top 5 matches
                output.append(f"\n  📄 {match['title']}")
                output.append(f"     File: {match['file']}")
                output.append(f"     Description: {match['description']}")
                if match["matched_keywords"]:
                    output.append(f"     Keywords: {', '.join(match['matched_keywords'])}")
                
                if detailed:
                    # Search within file content
                    file_path = self.api_patterns_root / match['file']
                    if file_path.exists():
                        content_matches = self.search_file_content(query, file_path)
                        if content_matches[:3]:  # Show first 3 matches
                            output.append(f"     Content matches:")
                            for line_num, line_content in content_matches[:3]:
                                output.append(f"       Line {line_num}: {line_content[:100]}...")
        else:
            output.append("❌ No matches found.")
            output.append("\n💡 Try searching for:")
            output.append("  • 'overview' - Pattern introduction")
            output.append("  • 'typeadapter' - Performance patterns")
            output.append("  • 'validation' - Field validation")
            output.append("  • 'collection' - Collection handling")
            output.append("  • 'example' - Implementation examples")
            output.append("  • 'migration' - Upgrade guide")
        
        return "\n".join(output)


def main():
    """Main search function."""
    parser = argparse.ArgumentParser(
        description="Search API Schema Patterns documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/search_documentation.py "typeadapter"
  python scripts/search_documentation.py "performance" --detailed
  python scripts/search_documentation.py "collection" --files-only
  python scripts/search_documentation.py "validation patterns"
        """
    )
    
    parser.add_argument("query", help="Search query")
    parser.add_argument("--detailed", "-d", action="store_true", 
                       help="Show detailed results with file content matches")
    parser.add_argument("--files-only", "-f", action="store_true",
                       help="Show only file matches without descriptions")
    
    args = parser.parse_args()
    
    # Find docs root
    current_dir = Path(__file__).parent.parent
    docs_root = current_dir / "docs"
    
    if not docs_root.exists():
        print(f"❌ Documentation directory not found: {docs_root}")
        return 1
    
    # Initialize searcher and search
    searcher = DocumentationSearcher(docs_root)
    results = searcher.search(args.query, args.detailed, args.files_only)
    
    # Display results
    formatted_results = searcher.format_results(results, args.detailed, args.files_only)
    print(formatted_results)
    
    return 0


if __name__ == "__main__":
    exit(main()) 