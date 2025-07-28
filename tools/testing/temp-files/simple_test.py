#!/usr/bin/env python
"""
Simple test to validate ambiguity detector without package dependencies.
"""
import sys
import os
sys.path.insert(0, 'src')

# Import specific modules directly
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Dict, Set, Optional
import re

# Copy the implementation directly to avoid import issues
class AmbiguityType(Enum):
    """Types of ambiguity that can be detected."""
    LINGUISTIC = auto()
    STRUCTURAL = auto()
    TECHNICAL = auto()

@dataclass
class AmbiguityInstance:
    """Represents a specific instance of ambiguity."""
    type: AmbiguityType
    term: str
    possible_meanings: List[str]
    context: str
    confidence: float  # 0.0 to 1.0

@dataclass
class AmbiguityAnalysis:
    """Results of ambiguity analysis."""
    is_ambiguous: bool
    ambiguity_score: float  # 0.0 to 1.0
    instances: List[AmbiguityInstance]
    details: Optional[str] = None

class AmbiguityDetector:
    """Detects various types of ambiguity in queries."""
    
    # Common ambiguous technical terms
    TECHNICAL_AMBIGUITIES = {
        'python': ['programming language', 'snake species'],
        'java': ['programming language', 'coffee', 'island'],
        'ruby': ['programming language', 'gemstone'],
        'shell': ['command interface', 'protective covering'],
        'thread': ['execution unit', 'fiber', 'sequence'],
        'memory': ['computer storage', 'human recall'],
        'cache': ['temporary storage', 'hidden supply'],
        'bug': ['software defect', 'insect'],
        'virus': ['malware', 'biological agent'],
        'port': ['network endpoint', 'physical connection', 'harbor'],
    }
    
    # Domain-specific term mappings
    DOMAIN_TERMS = {
        'programming': {
            'class': 'object template',
            'object': 'instance of class',
            'method': 'function in class',
            'constructor': 'initialization method',
        },
        'networking': {
            'address': 'network location',
            'protocol': 'communication rules',
            'packet': 'data unit',
            'socket': 'endpoint pair',
        },
        'system': {
            'process': 'running program',
            'thread': 'execution unit',
            'buffer': 'temporary storage',
            'handle': 'resource reference',
        }
    }
    
    # Patterns indicating structural ambiguity
    STRUCTURAL_PATTERNS = [
        r'(and|or)(?:\s+\w+){3,}',  # Multiple items in conjunction/disjunction
        r'\b(it|this|that|these|those)\b(?!\s+\w+\s+\w+)',  # Unclear references
        r'(?:compare|versus|vs).*?and.*?(?:with|to)',  # Complex comparisons
        r'\?.*\?',  # Multiple questions
    ]
    
    def __init__(self):
        """Initialize the AmbiguityDetector."""
        self.structural_regex = [re.compile(p, re.IGNORECASE) for p in self.STRUCTURAL_PATTERNS]
        # Create reverse mapping for domain terms
        self.term_to_domain = {}
        for domain, terms in self.DOMAIN_TERMS.items():
            for term in terms:
                if term not in self.term_to_domain:
                    self.term_to_domain[term] = set()
                self.term_to_domain[term].add(domain)
    
    def analyze_ambiguity(self, text: str) -> AmbiguityAnalysis:
        """
        Analyze text for various types of ambiguity.
        
        Args:
            text: The text to analyze
            
        Returns:
            AmbiguityAnalysis containing detected ambiguities
        """
        instances = []
        
        # Check for linguistic ambiguity
        linguistic_instances = self._detect_linguistic_ambiguity(text)
        instances.extend(linguistic_instances)
        
        # Check for structural ambiguity
        structural_instances = self._detect_structural_ambiguity(text)
        instances.extend(structural_instances)
        
        # Check for technical ambiguity
        technical_instances = self._detect_technical_ambiguity(text)
        instances.extend(technical_instances)
        
        # Calculate overall ambiguity score
        ambiguity_score = self._calculate_ambiguity_score(instances)
        
        # Generate detailed analysis
        details = self._generate_ambiguity_details(instances) if instances else None
        
        return AmbiguityAnalysis(
            is_ambiguous=len(instances) > 0,
            ambiguity_score=ambiguity_score,
            instances=instances,
            details=details
        )
    
    def _detect_linguistic_ambiguity(self, text: str) -> List[AmbiguityInstance]:
        """Detect linguistic ambiguity in text."""
        instances = []
        words = set(re.findall(r'\b\w+\b', text.lower()))
        
        # Check for ambiguous technical terms
        for term, meanings in self.TECHNICAL_AMBIGUITIES.items():
            if term in words:
                context = self._extract_context(text, term)
                instances.append(AmbiguityInstance(
                    type=AmbiguityType.LINGUISTIC,
                    term=term,
                    possible_meanings=meanings,
                    context=context,
                    confidence=0.8  # High confidence for known ambiguous terms
                ))
        
        return instances
    
    def _detect_structural_ambiguity(self, text: str) -> List[AmbiguityInstance]:
        """Detect structural ambiguity in text."""
        instances = []
        
        for pattern in self.structural_regex:
            matches = pattern.finditer(text)
            for match in matches:
                context = self._extract_context(text, match.group())
                instances.append(AmbiguityInstance(
                    type=AmbiguityType.STRUCTURAL,
                    term=match.group(),
                    possible_meanings=['Multiple interpretations possible'],
                    context=context,
                    confidence=0.7
                ))
        
        return instances
    
    def _detect_technical_ambiguity(self, text: str) -> List[AmbiguityInstance]:
        """Detect technical ambiguity in text."""
        instances = []
        words = set(re.findall(r'\b\w+\b', text.lower()))
        
        # Check for terms with multiple domain meanings
        for term, domains in self.term_to_domain.items():
            if term in words and len(domains) > 1:
                context = self._extract_context(text, term)
                meanings = [f"{domain}: {self.DOMAIN_TERMS[domain][term]}"
                          for domain in domains]
                instances.append(AmbiguityInstance(
                    type=AmbiguityType.TECHNICAL,
                    term=term,
                    possible_meanings=meanings,
                    context=context,
                    confidence=0.9  # Very high confidence for domain-specific terms
                ))
        
        return instances
    
    def _extract_context(self, text: str, term: str, window: int = 50) -> str:
        """Extract surrounding context for a term."""
        term_pos = text.lower().find(term.lower())
        if term_pos == -1:
            return ""
        
        start = max(0, term_pos - window)
        end = min(len(text), term_pos + len(term) + window)
        
        context = text[start:end].strip()
        if start > 0:
            context = f"...{context}"
        if end < len(text):
            context = f"{context}..."
            
        return context
    
    def _calculate_ambiguity_score(self, instances: List[AmbiguityInstance]) -> float:
        """Calculate overall ambiguity score."""
        if not instances:
            return 0.0
            
        # Weight different types of ambiguity
        weights = {
            AmbiguityType.LINGUISTIC: 0.3,
            AmbiguityType.STRUCTURAL: 0.4,
            AmbiguityType.TECHNICAL: 0.3
        }
        
        # Calculate weighted average of instance confidences
        weighted_sum = sum(
            instance.confidence * weights[instance.type]
            for instance in instances
        )
        
        # Normalize by number of instances and maximum possible score
        max_score = sum(weights.values())
        return min(weighted_sum / max_score, 1.0)
    
    def _generate_ambiguity_details(self, instances: List[AmbiguityInstance]) -> str:
        """Generate detailed explanation of ambiguity analysis."""
        if not instances:
            return "No ambiguity detected"
            
        details = ["Ambiguity Analysis:"]
        
        # Group instances by type
        by_type = {}
        for instance in instances:
            if instance.type not in by_type:
                by_type[instance.type] = []
            by_type[instance.type].append(instance)
            
        # Generate details for each type
        for ambiguity_type, type_instances in by_type.items():
            details.append(f"\n{ambiguity_type.name} Ambiguity:")
            for instance in type_instances:
                details.append(f"- Term: {instance.term}")
                details.append(f"  Context: {instance.context}")
                details.append(f"  Possible meanings:")
                for meaning in instance.possible_meanings:
                    details.append(f"    * {meaning}")
                    
        return "\n".join(details)

def run_comprehensive_test():
    """Run comprehensive tests mimicking the original test file."""
    detector = AmbiguityDetector()
    test_results = []
    
    # Test 1: Linguistic ambiguity
    print("=== Test 1: Linguistic Ambiguity ===")
    queries = [
        "How do I handle python installation?",
        "What is the best way to learn java?",
        "Can you explain what a shell is?",
    ]
    
    for query in queries:
        result = detector.analyze_ambiguity(query)
        print(f"Query: {query}")
        print(f"  Ambiguous: {result.is_ambiguous}")
        print(f"  Score: {result.ambiguity_score}")
        print(f"  Instances: {len(result.instances)}")
        
        # Check assertions
        linguistic_found = any(instance.type == AmbiguityType.LINGUISTIC for instance in result.instances)
        test_results.append({
            'test': 'linguistic',
            'query': query,
            'is_ambiguous': result.is_ambiguous,
            'has_linguistic': linguistic_found,
            'score_positive': result.ambiguity_score > 0.0
        })
    
    # Test 2: Structural ambiguity
    print("\n=== Test 2: Structural Ambiguity ===")
    queries = [
        "Compare Python, Java, and Ruby with C++ and JavaScript",
        "It crashed when running the process",
        "Should I use MySQL or PostgreSQL and MongoDB or Redis?",
    ]
    
    for query in queries:
        result = detector.analyze_ambiguity(query)
        print(f"Query: {query}")
        print(f"  Ambiguous: {result.is_ambiguous}")
        print(f"  Score: {result.ambiguity_score}")
        print(f"  Instances: {len(result.instances)}")
        
        structural_found = any(instance.type == AmbiguityType.STRUCTURAL for instance in result.instances)
        test_results.append({
            'test': 'structural',
            'query': query,
            'is_ambiguous': result.is_ambiguous,
            'has_structural': structural_found,
            'score_positive': result.ambiguity_score > 0.0
        })
    
    # Test 3: Technical ambiguity
    print("\n=== Test 3: Technical Ambiguity ===")
    queries = [
        "How do I create a new thread?",
        "What is the best way to handle memory management?",
        "Can you explain how the cache works?",
    ]
    
    for query in queries:
        result = detector.analyze_ambiguity(query)
        print(f"Query: {query}")
        print(f"  Ambiguous: {result.is_ambiguous}")
        print(f"  Score: {result.ambiguity_score}")
        print(f"  Instances: {len(result.instances)}")
        
        technical_found = any(instance.type == AmbiguityType.TECHNICAL for instance in result.instances)
        test_results.append({
            'test': 'technical',
            'query': query,
            'is_ambiguous': result.is_ambiguous,
            'has_technical': technical_found,
            'score_positive': result.ambiguity_score > 0.0
        })
    
    # Test 4: Unambiguous input
    print("\n=== Test 4: Unambiguous Input ===")
    queries = [
        "What is the current time?",
        "Show me today's weather forecast.",
        "Calculate 2 plus 2.",
    ]
    
    for query in queries:
        result = detector.analyze_ambiguity(query)
        print(f"Query: {query}")
        print(f"  Ambiguous: {result.is_ambiguous}")
        print(f"  Score: {result.ambiguity_score}")
        print(f"  Instances: {len(result.instances)}")
        
        test_results.append({
            'test': 'unambiguous',
            'query': query,
            'is_ambiguous': result.is_ambiguous,
            'instances_empty': len(result.instances) == 0,
            'score_zero': result.ambiguity_score == 0.0
        })
    
    # Analysis
    print("\n=== Test Results Summary ===")
    passed = 0
    total = 0
    
    for result in test_results:
        total += 1
        test_name = result['test']
        
        if test_name in ['linguistic', 'structural', 'technical']:
            expected_type_key = f"has_{test_name}"
            if (result['is_ambiguous'] and result[expected_type_key] and result['score_positive']):
                passed += 1
                print(f"✓ {test_name}: {result['query'][:30]}...")
            else:
                print(f"✗ {test_name}: {result['query'][:30]}... - Expected ambiguous with {test_name} type")
        elif test_name == 'unambiguous':
            if (not result['is_ambiguous'] and result['instances_empty'] and result['score_zero']):
                passed += 1
                print(f"✓ unambiguous: {result['query'][:30]}...")
            else:
                print(f"✗ unambiguous: {result['query'][:30]}... - Expected no ambiguity")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    return passed, total

if __name__ == "__main__":
    passed, total = run_comprehensive_test()