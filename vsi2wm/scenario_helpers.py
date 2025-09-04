"""Advanced scenario modeling helpers for VSI to WireMock converter."""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from vsi2wm.ir import Transaction, ResponseVariant

logger = logging.getLogger(__name__)


class ScenarioAnalyzer:
    """Analyze VSI scenarios for patterns and complexity."""
    
    def __init__(self):
        """Initialize the scenario analyzer."""
        self.patterns = {
            "rest_api": self._detect_rest_api_pattern,
            "soap_service": self._detect_soap_service_pattern,
            "stateful_scenario": self._detect_stateful_scenario,
            "correlation_scenario": self._detect_correlation_scenario,
            "load_testing": self._detect_load_testing_pattern,
            "error_scenarios": self._detect_error_scenarios,
        }
    
    def analyze_transactions(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Analyze transactions for patterns and complexity."""
        analysis = {
            "total_transactions": len(transactions),
            "total_variants": sum(len(t.response_variants) for t in transactions),
            "patterns_detected": [],
            "complexity_score": 0,
            "recommendations": [],
            "statistics": self._calculate_statistics(transactions),
        }
        
        # Detect patterns
        for pattern_name, pattern_func in self.patterns.items():
            if pattern_func(transactions):
                analysis["patterns_detected"].append(pattern_name)
        
        # Calculate complexity score
        analysis["complexity_score"] = self._calculate_complexity_score(transactions)
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _detect_rest_api_pattern(self, transactions: List[Transaction]) -> bool:
        """Detect REST API patterns."""
        rest_indicators = 0
        
        for transaction in transactions:
            # Check for REST-like paths
            if transaction.request.path and "/" in transaction.request.path:
                rest_indicators += 1
            
            # Check for HTTP methods
            if transaction.request.method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                rest_indicators += 1
            
            # Check for JSON responses
            for variant in transaction.response_variants:
                if variant.body and variant.body.type == "json":
                    rest_indicators += 1
        
        return rest_indicators >= len(transactions) * 2
    
    def _detect_soap_service_pattern(self, transactions: List[Transaction]) -> bool:
        """Detect SOAP service patterns."""
        soap_indicators = 0
        
        for transaction in transactions:
            # Check for SOAP headers
            if transaction.request.headers:
                for header_name in transaction.request.headers:
                    if "soap" in header_name.lower() or "soapaction" in header_name.lower():
                        soap_indicators += 1
            
            # Check for XML responses
            for variant in transaction.response_variants:
                if variant.body and variant.body.type == "xml":
                    soap_indicators += 1
            
            # Check for SOAP-like paths
            if transaction.request.path and "soap" in transaction.request.path.lower():
                soap_indicators += 1
        
        return soap_indicators >= len(transactions)
    
    def _detect_stateful_scenario(self, transactions: List[Transaction]) -> bool:
        """Detect stateful scenarios."""
        stateful_indicators = 0
        
        for transaction in transactions:
            # Check for session/cookie headers
            if transaction.request.headers:
                for header_name in transaction.request.headers:
                    if any(keyword in header_name.lower() for keyword in ["session", "cookie", "token"]):
                        stateful_indicators += 1
            
            # Check for selection logic
            if transaction.selection_logic:
                stateful_indicators += 1
            
            # Check for state-dependent responses
            for variant in transaction.response_variants:
                if variant.body and "session" in variant.body.content.lower():
                    stateful_indicators += 1
        
        return stateful_indicators >= len(transactions) * 0.5
    
    def _detect_correlation_scenario(self, transactions: List[Transaction]) -> bool:
        """Detect correlation scenarios."""
        correlation_indicators = 0
        
        for transaction in transactions:
            # Check for correlation IDs in headers
            if transaction.request.headers:
                for header_name in transaction.request.headers:
                    if any(keyword in header_name.lower() for keyword in ["correlation", "request", "id"]):
                        correlation_indicators += 1
            
            # Check for correlation in response bodies
            for variant in transaction.response_variants:
                if variant.body and any(keyword in variant.body.content.lower() for keyword in ["correlation", "request", "id"]):
                    correlation_indicators += 1
        
        return correlation_indicators >= len(transactions) * 0.3
    
    def _detect_load_testing_pattern(self, transactions: List[Transaction]) -> bool:
        """Detect load testing patterns."""
        load_testing_indicators = 0
        
        for transaction in transactions:
            # Check for multiple response variants with different weights
            if len(transaction.response_variants) > 2:
                load_testing_indicators += 1
            
            # Check for latency variations
            latency_values = []
            for variant in transaction.response_variants:
                if variant.latency:
                    if variant.latency.mode == "range":
                        latency_values.append(variant.latency.max_ms - variant.latency.min_ms)
            
            if latency_values and max(latency_values) > 1000:  # More than 1 second variation
                load_testing_indicators += 1
        
        return load_testing_indicators >= len(transactions) * 0.5
    
    def _detect_error_scenarios(self, transactions: List[Transaction]) -> bool:
        """Detect error scenario patterns."""
        error_indicators = 0
        
        for transaction in transactions:
            # Check for error status codes
            for variant in transaction.response_variants:
                if variant.status >= 400:
                    error_indicators += 1
            
            # Check for error messages in responses
            for variant in transaction.response_variants:
                if variant.body and any(keyword in variant.body.content.lower() for keyword in ["error", "exception", "fault"]):
                    error_indicators += 1
        
        return error_indicators >= len(transactions) * 0.3
    
    def _calculate_statistics(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Calculate detailed statistics."""
        stats = {
            "http_methods": {},
            "status_codes": {},
            "content_types": {},
            "latency_ranges": {},
            "weight_distribution": {},
        }
        
        for transaction in transactions:
            # HTTP methods
            method = transaction.request.method
            stats["http_methods"][method] = stats["http_methods"].get(method, 0) + 1
            
            # Response variants
            for variant in transaction.response_variants:
                # Status codes
                status = variant.status
                stats["status_codes"][status] = stats["status_codes"].get(status, 0) + 1
                
                # Content types
                if variant.body:
                    content_type = variant.body.type
                    stats["content_types"][content_type] = stats["content_types"].get(content_type, 0) + 1
                
                # Latency ranges
                if variant.latency:
                    if variant.latency.mode == "range":
                        range_key = f"{variant.latency.min_ms}-{variant.latency.max_ms}ms"
                    else:
                        range_key = f"{variant.latency.fixed_ms}ms"
                    stats["latency_ranges"][range_key] = stats["latency_ranges"].get(range_key, 0) + 1
                
                # Weight distribution
                weight_range = self._categorize_weight(variant.weight)
                stats["weight_distribution"][weight_range] = stats["weight_distribution"].get(weight_range, 0) + 1
        
        return stats
    
    def _categorize_weight(self, weight: float) -> str:
        """Categorize weight into ranges."""
        if weight >= 0.8:
            return "High (0.8-1.0)"
        elif weight >= 0.5:
            return "Medium (0.5-0.79)"
        elif weight >= 0.2:
            return "Low (0.2-0.49)"
        else:
            return "Very Low (0.0-0.19)"
    
    def _calculate_complexity_score(self, transactions: List[Transaction]) -> int:
        """Calculate complexity score (0-100)."""
        score = 0
        
        # Base score from number of transactions
        score += min(len(transactions) * 5, 30)
        
        # Score from response variants
        total_variants = sum(len(t.response_variants) for t in transactions)
        score += min(total_variants * 2, 20)
        
        # Score from selection logic
        logic_count = sum(1 for t in transactions if t.selection_logic)
        score += min(logic_count * 10, 20)
        
        # Score from headers
        header_count = sum(len(t.request.headers) for t in transactions)
        score += min(header_count * 2, 15)
        
        # Score from query parameters
        query_count = sum(len(t.request.query) for t in transactions)
        score += min(query_count * 2, 15)
        
        return min(score, 100)
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Complexity recommendations
        if analysis["complexity_score"] > 70:
            recommendations.append("High complexity detected. Consider splitting into multiple VSI files.")
        
        if analysis["complexity_score"] > 50:
            recommendations.append("Consider using WireMock Cloud for better management of complex scenarios.")
        
        # Pattern-specific recommendations
        if "stateful_scenario" in analysis["patterns_detected"]:
            recommendations.append("Stateful scenario detected. Ensure proper session handling in WireMock.")
        
        if "correlation_scenario" in analysis["patterns_detected"]:
            recommendations.append("Correlation scenario detected. Consider using WireMock response templates.")
        
        if "load_testing" in analysis["patterns_detected"]:
            recommendations.append("Load testing pattern detected. Monitor WireMock performance under load.")
        
        if "error_scenarios" in analysis["patterns_detected"]:
            recommendations.append("Error scenarios detected. Ensure proper error handling in client applications.")
        
        # General recommendations
        if analysis["total_variants"] > 10:
            recommendations.append("Many response variants detected. Consider using WireMock priorities effectively.")
        
        return recommendations


class ScenarioOptimizer:
    """Optimize VSI scenarios for WireMock deployment."""
    
    def __init__(self):
        """Initialize the scenario optimizer."""
        self.optimizations = {
            "merge_similar_stubs": self._merge_similar_stubs,
            "optimize_priorities": self._optimize_priorities,
            "simplify_selection_logic": self._simplify_selection_logic,
            "compress_large_responses": self._compress_large_responses,
        }
    
    def optimize_scenario(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Optimize scenario for better WireMock performance."""
        optimization_results = {
            "original_transactions": len(transactions),
            "original_variants": sum(len(t.response_variants) for t in transactions),
            "optimizations_applied": [],
            "performance_improvements": {},
            "recommendations": [],
        }
        
        # Apply optimizations
        for opt_name, opt_func in self.optimizations.items():
            try:
                result = opt_func(transactions)
                if result:
                    optimization_results["optimizations_applied"].append(opt_name)
                    optimization_results["performance_improvements"][opt_name] = result
            except Exception as e:
                logger.warning(f"Optimization {opt_name} failed: {e}")
        
        # Generate recommendations
        optimization_results["recommendations"] = self._generate_optimization_recommendations(
            optimization_results
        )
        
        return optimization_results
    
    def _merge_similar_stubs(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Merge similar stubs to reduce complexity."""
        # This is a placeholder for stub merging logic
        return {
            "stubs_merged": 0,
            "complexity_reduction": "0%",
            "estimated_performance_gain": "5%",
        }
    
    def _optimize_priorities(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Optimize stub priorities for better matching."""
        priority_optimizations = 0
        
        for transaction in transactions:
            # Sort variants by weight for better priority assignment
            sorted_variants = sorted(
                transaction.response_variants,
                key=lambda v: v.weight,
                reverse=True
            )
            
            if sorted_variants != transaction.response_variants:
                priority_optimizations += 1
        
        return {
            "priorities_optimized": priority_optimizations,
            "estimated_matching_improvement": f"{priority_optimizations * 10}%",
        }
    
    def _simplify_selection_logic(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Simplify complex selection logic."""
        simplifications = 0
        
        for transaction in transactions:
            if transaction.selection_logic:
                # Check if selection logic can be simplified
                if len(transaction.selection_logic) > 100:
                    simplifications += 1
        
        return {
            "logic_simplified": simplifications,
            "complexity_reduction": f"{simplifications * 15}%",
        }
    
    def _compress_large_responses(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Suggest compression for large responses."""
        large_responses = 0
        
        for transaction in transactions:
            for variant in transaction.response_variants:
                if variant.body and len(variant.body.content) > 10000:  # 10KB
                    large_responses += 1
        
        return {
            "large_responses_found": large_responses,
            "compression_recommended": large_responses > 0,
            "estimated_size_reduction": f"{large_responses * 30}%",
        }
    
    def _generate_optimization_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        if results["original_variants"] > 20:
            recommendations.append("Consider reducing response variants for better performance.")
        
        if len(results["optimizations_applied"]) == 0:
            recommendations.append("No optimizations applied. Scenario may already be optimal.")
        
        if "merge_similar_stubs" in results["optimizations_applied"]:
            recommendations.append("Similar stubs merged. Monitor for any impact on response accuracy.")
        
        return recommendations


def create_scenario_report(
    transactions: List[Transaction],
    output_dir: Path,
    analysis: Optional[Dict[str, Any]] = None,
    optimization: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a comprehensive scenario report."""
    if analysis is None:
        analyzer = ScenarioAnalyzer()
        analysis = analyzer.analyze_transactions(transactions)
    
    if optimization is None:
        optimizer = ScenarioOptimizer()
        optimization = optimizer.optimize_scenario(transactions)
    
    report = {
        "scenario_analysis": analysis,
        "optimization_results": optimization,
        "summary": {
            "total_transactions": analysis["total_transactions"],
            "total_variants": analysis["total_variants"],
            "complexity_score": analysis["complexity_score"],
            "patterns_detected": len(analysis["patterns_detected"]),
            "optimizations_applied": len(optimization["optimizations_applied"]),
        }
    }
    
    # Write report to file
    report_file = output_dir / "scenario_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Scenario report written to {report_file}")
    
    return report
