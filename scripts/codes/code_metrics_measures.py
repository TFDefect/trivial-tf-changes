import json
import os
import subprocess
import tempfile
from typing import Dict, List

from typing import Dict, List
import sys
import os

# Add local directory to path for imports if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from scripts.codes.base_metrics_extractor import BaseMetricsExtractor
except ImportError:
    # Try relative import or different path structure
    try:
        from base_metrics_extractor import BaseMetricsExtractor
    except ImportError:
        # Define a dummy base class if missing to avoid crash given we might verify structure later
        class BaseMetricsExtractor:
            pass

# Mock logger since utils might be missing
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CodeMetricsExtractor")


class CodeMetricsExtractor(BaseMetricsExtractor):
    """
    Class for running TerraMetrics and extracting metrics from modified Terraform blocks.
    """

    def __init__(self, jar_path: str = "libs/terraform_metrics-1.0.jar"):
        """
        Initializes the metrics extractor.

        Args:
            jar_path (str): Path to the TerraMetrics JAR file.
        """
        self.jar_path = jar_path
        if not os.path.exists(self.jar_path):
            raise FileNotFoundError(f"TerraMetrics JAR introuvable : {self.jar_path}")

    def extract_metrics(self, modified_blocks: Dict[str, List[str]]) -> Dict[str, dict]:
        """
        Runs TerraMetrics on modified Terraform blocks and extracts metrics.

        Args:
            modified_blocks (Dict[str, List[str]]): Files and their modified blocks.

        Returns:
            Dict[str, dict]: Extracted metrics for each file.
        """
        if not modified_blocks:
            logger.warning("Aucun bloc Terraform à analyser.")
            return {}

        metrics_results = {}

        for file_name, blocks in modified_blocks.items():
            try:
                tf_path, json_path = self._create_temp_files(blocks)
                self._run_terrametrics(tf_path, json_path)

                if os.path.exists(json_path):
                    with open(json_path, "r") as f:
                        metrics_results[file_name] = json.load(f)
                else:
                    logger.error(f"JSON file not generated for {file_name}.")

            except subprocess.CalledProcessError as e:
                logger.error(f"TerraMetrics error ({file_name}): {e}")
                metrics_results[file_name] = {"error": "TerraMetrics execution failed"}

            except Exception as e:
                logger.error(f"Unexpected error ({file_name}): {e}")
                metrics_results[file_name] = {"error": str(e)}

            finally:
                self._cleanup_temp_files([tf_path, json_path])

        return metrics_results

    def _create_temp_files(self, blocks: List[str]) -> tuple:
        """
        Creates temporary Terraform (.tf) and output (.json) files.

        Args:
            blocks (List[str]): List of blocks to write.

        Returns:
            Tuple[str, str]: Paths of the .tf and .json files.
        """
        tf_file = tempfile.NamedTemporaryFile(suffix=".tf", delete=False, mode="w")
        json_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)

        tf_file.write("\n\n".join(blocks))
        tf_file.close()

        return tf_file.name, json_file.name

    def _run_terrametrics(self, tf_path: str, output_path: str):
        """
        Runs TerraMetrics for a given file.

        Args:
            tf_path (str): Path of the Terraform file.
            output_path (str): Path of the JSON output file.
        """
        command = [
            "java",
            "-jar",
            self.jar_path,
            "--file",
            tf_path,
            "-b",
            "--target",
            output_path,
        ]

        logger.info(f"[CODE] Exécution de TerraMetrics pour {tf_path}...")
        subprocess.run(command, check=True)

    def _cleanup_temp_files(self, file_paths: List[str]):
        """
        Deletes temporary files.

        Args:
            file_paths (List[str]): Paths of the files to delete.
        """
        for path in file_paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    logger.warning(f"Impossible de supprimer {path} : {e}")
