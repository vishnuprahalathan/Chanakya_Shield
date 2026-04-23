import numpy as np

class RealTimePacketMetricEngine:
    def __init__(self, name="Generic"):
        self.name = name
        self.tp = 0
        self.fp = 0
        self.tn = 0
        self.fn = 0
        self.total_packets = 0
        self.start_time = None
        self.latencies = []
        self.confidences = []

    def reset(self):
        self.tp = 0
        self.fp = 0
        self.tn = 0
        self.fn = 0
        self.total_packets = 0
        self.latencies = []
        self.confidences = []
        self.start_time = None

    def update(self, y_true, y_pred, latency_ms, confidence):
        """
        Updates metrics based on a single packet result.
        y_true: 1 for Attack, 0 for Benign
        y_pred: 1 for Attack, 0 for Benign
        """
        self.total_packets += 1
        self.latencies.append(latency_ms)
        self.confidences.append(confidence)

        # Keep lists from growing indefinitely for memory safety
        if len(self.latencies) > 10000:
            self.latencies.pop(0)
            self.confidences.pop(0)

        if y_true == 1 and y_pred == 1:
            self.tp += 1
        elif y_true == 0 and y_pred == 1:
            self.fp += 1
        elif y_true == 0 and y_pred == 0:
            self.tn += 1
        elif y_true == 1 and y_pred == 0:
            self.fn += 1

    def get_metrics(self):
        accuracy = (self.tp + self.tn) / max(1, self.total_packets)
        precision = self.tp / max(1, self.tp + self.fp)
        recall = self.tp / max(1, self.tp + self.fn)
        f1 = 2 * (precision * recall) / max(1e-9, precision + recall)
        
        # False Positive Rate: FP / (FP + TN)
        fpr = self.fp / max(1, self.fp + self.tn)
        
        # False Negative Rate: FN / (TP + FN)
        fnr = self.fn / max(1, self.tp + self.fn)

        avg_latency = np.mean(self.latencies) if self.latencies else 0
        avg_confidence = np.mean(self.confidences) if self.confidences else 0
        confidence_variance = np.var(self.confidences) if self.confidences else 0

        return {
            "name": self.name,
            "accuracy": round(accuracy * 100, 2),
            "precision": round(precision * 100, 2),
            "recall": round(recall * 100, 2),
            "f1": round(f1 * 100, 2),
            "fpr": round(fpr * 100, 4),
            "fnr": round(fnr * 100, 4),
            "avg_latency": round(avg_latency, 3),
            "avg_confidence": round(avg_confidence, 3),
            "confidence_variance": round(confidence_variance, 4),
            "total_packets": self.total_packets
        }
