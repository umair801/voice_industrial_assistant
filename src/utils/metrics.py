"""
Metrics Collection and Reporting
Tracks performance and usage metrics
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import numpy as np
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and reports system metrics"""
    
    def __init__(self, output_dir: str = "logs/metrics"):
        """
        Initialize metrics collector
        
        Args:
            output_dir: Directory for metrics files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics = {
            "interactions": [],
            "recognition_accuracy": [],
            "task_completion_time": [],
            "intent_distribution": {},
            "error_count": 0,
            "start_time": datetime.now().isoformat()
        }
        
        logger.info("Metrics collector initialized")
    
    def log_interaction(
        self,
        command: str,
        intent: str,
        success: bool,
        latency: float,
        stt_confidence: float
    ):
        """
        Log voice interaction
        
        Args:
            command: Voice command text
            intent: Detected intent
            success: Whether interaction succeeded
            latency: Processing latency in seconds
            stt_confidence: STT confidence score
        """
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "intent": intent,
            "success": success,
            "latency": latency,
            "stt_confidence": stt_confidence
        }
        
        self.metrics["interactions"].append(interaction)
        self.metrics["recognition_accuracy"].append(stt_confidence)
        self.metrics["task_completion_time"].append(latency)
        
        # Update intent distribution
        if intent not in self.metrics["intent_distribution"]:
            self.metrics["intent_distribution"][intent] = 0
        self.metrics["intent_distribution"][intent] += 1
        
        if not success:
            self.metrics["error_count"] += 1
        
        logger.debug(f"Logged interaction: {intent} (success: {success})")
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics
        
        Returns:
            Summary dictionary
        """
        total_interactions = len(self.metrics["interactions"])
        
        if total_interactions == 0:
            return {
                "total_interactions": 0,
                "error_rate": 0.0,
                "avg_latency": 0.0,
                "avg_stt_confidence": 0.0
            }
        
        successful = sum(1 for i in self.metrics["interactions"] if i["success"])
        
        return {
            "total_interactions": total_interactions,
            "successful_interactions": successful,
            "error_rate": self.metrics["error_count"] / total_interactions,
            "success_rate": successful / total_interactions,
            "avg_latency": np.mean(self.metrics["task_completion_time"]),
            "median_latency": np.median(self.metrics["task_completion_time"]),
            "avg_stt_confidence": np.mean(self.metrics["recognition_accuracy"]),
            "intent_distribution": self.metrics["intent_distribution"],
            "uptime_hours": self._calculate_uptime()
        }
    
    def _calculate_uptime(self) -> float:
        """Calculate uptime in hours"""
        start = datetime.fromisoformat(self.metrics["start_time"])
        now = datetime.now()
        delta = now - start
        return delta.total_seconds() / 3600
    
    def save_report(self, filename: str = None):
        """
        Save metrics report to file
        
        Args:
            filename: Output filename (auto-generated if None)
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_report_{timestamp}.json"
        
        output_file = self.output_dir / filename
        
        report = {
            "summary": self.get_summary(),
            "detailed_metrics": self.metrics
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Metrics report saved to {output_file}")
        
        return output_file
    
    def print_summary(self):
        """Print summary to console"""
        summary = self.get_summary()
        
        print("\n" + "="*50)
        print("VOICE ASSISTANT METRICS SUMMARY")
        print("="*50)
        print(f"Total Interactions: {summary['total_interactions']}")
        print(f"Success Rate: {summary['success_rate']*100:.1f}%")
        print(f"Error Rate: {summary['error_rate']*100:.1f}%")
        print(f"Avg Latency: {summary['avg_latency']:.2f}s")
        print(f"Median Latency: {summary['median_latency']:.2f}s")
        print(f"Avg STT Confidence: {summary['avg_stt_confidence']*100:.1f}%")
        print(f"Uptime: {summary['uptime_hours']:.2f} hours")
        
        print("\nIntent Distribution:")
        for intent, count in summary['intent_distribution'].items():
            percentage = (count / summary['total_interactions']) * 100
            print(f"  {intent}: {count} ({percentage:.1f}%)")
        
        print("="*50 + "\n")


if __name__ == "__main__":
    # Test metrics collector
    metrics = MetricsCollector()
    
    # Simulate interactions
    metrics.log_interaction(
        command="Check stock for SKU AB-123",
        intent="query_inventory",
        success=True,
        latency=1.5,
        stt_confidence=0.95
    )
    
    metrics.log_interaction(
        command="Add 50 units to B7-2",
        intent="update_inventory",
        success=True,
        latency=2.1,
        stt_confidence=0.88
    )
    
    # Print summary
    metrics.print_summary()
    
    # Save report
    metrics.save_report()
