from abc import ABC, abstractmethod
from typing import Dict, List


class BaseMetricsExtractor(ABC):
    """
    Abstract class for Terraform metrics extractors.
    """

    @abstractmethod
    def extract_metrics(self, modified_blocks: Dict[str, List[str]]) -> Dict[str, dict]:
        """
        Abstract method to extract metrics from modified Terraform blocks.

        Args:
            modified_blocks (Dict[str, List[str]]): Dictionary of files and their modified blocks.

        Returns:
            Dict[str, dict]: Dictionary containing the extracted metrics.
        """
        pass
