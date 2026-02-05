
import os
import sys
import json

# Ensure project root is on sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.codes.code_metrics_measures import CodeMetricsExtractor

def test_metrics_extraction():
    print("Testing CodeMetricsExtractor...")
    
    # Path to JAR
    jar_path = os.path.join(os.getcwd(), "libs", "terraform_metrics-1.0.jar")
    extractor = CodeMetricsExtractor(jar_path=jar_path)
    
    # Sample Terraform Code
    tf_code = """
    resource "google_compute_instance" "default" {
      name         = "test"
      machine_type = "e2-medium"
      zone         = "us-central1-a"

      boot_disk {
        initialize_params {
          image = "debian-cloud/debian-11"
        }
      }

      network_interface {
        network = "default"
      }
    }
    """
    
    # We need to simulate how the extractor is used.
    # The current CodeMetricsExtractor.extract_metrics expects {filename: [blocks]}
    # Let's try to use the internal method _run_terrametrics via a helper wrapper 
    # similar to what we did in ImpactedBlocks or use extract_metrics directly if we treat the code as a block.
    
    # Let's treat the tf_code as a "block" content for valid testing of the public API
    modified_blocks = {"sample.tf": [tf_code]}
    
    print("running extract_metrics...")
    try:
        results = extractor.extract_metrics(modified_blocks)
        
        print("\n___ Results ___")
        print(json.dumps(results, indent=2))
        
        if "sample.tf" in results:
            data = results["sample.tf"]
            # verify we have some metrics
            # The structure depends on what the JAR returns. 
            # Usually it returns a dict with "data" (blocks) and "head" (file metrics)
            
            if "data" in data and len(data["data"]) > 0:
                print("\n✅ Success: Metrics extracted for blocks.")
                block = data["data"][0]
                print(f"Block Identifier: {block.get('block_identifiers')}")
                print(f"Metrics keys found: {list(block.keys())}")
            else:
                 print("\n⚠️ Warning: No blocks found in data.")
                 
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_metrics_extraction()
