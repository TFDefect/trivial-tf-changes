import unittest
import os
import sys
import tempfile
import csv
from datetime import datetime

sys.path.append(os.getcwd())

from scripts.collect_metrics import load_history_from_csv

class TestHistoryLoading(unittest.TestCase):
    
    def test_load_history_from_csv(self):
        """
        Test loading previous contributions and author experience from CSV.
        """
        # Create a temporary CSV with sample data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['commit', 'author', 'date', 'file', 'block_identifiers', 'numAttrs'])
            writer.writeheader()
            writer.writerow({
                'commit': 'abc123',
                'author': 'alice',
                'date': '2024-01-01T10:00:00',
                'file': 'main.tf',
                'block_identifiers': 'resource.foo',
                'numAttrs': '5'
            })
            writer.writerow({
                'commit': 'abc123',
                'author': 'alice',
                'date': '2024-01-01T10:00:00',
                'file': 'main.tf',
                'block_identifiers': 'resource.bar',
                'numAttrs': '3'
            })
            writer.writerow({
                'commit': 'def456',
                'author': 'bob',
                'date': '2024-01-02T11:00:00',
                'file': 'variables.tf',
                'block_identifiers': 'variable.region',
                'numAttrs': '1'
            })
            writer.writerow({
                'commit': 'ghi789',
                'author': 'alice',
                'date': '2024-01-03T12:00:00',
                'file': 'main.tf',
                'block_identifiers': 'module.app',
                'numAttrs': '7'
            })
            temp_path = f.name
        
        try:
            # Load history
            contributions, author_exp = load_history_from_csv(temp_path)
            
            # Verify contributions loaded
            self.assertEqual(len(contributions), 4, "Should load 4 contributions")
            
            # Verify author experience (unique commits per author)
            self.assertEqual(author_exp['alice'], 2, "Alice has 2 unique commits")
            self.assertEqual(author_exp['bob'], 1, "Bob has 1 unique commit")
            
            # Verify data structure
            self.assertEqual(contributions[0]['author'], 'alice')
            self.assertEqual(contributions[0]['block_identifiers'], 'resource.foo')
            
        finally:
            os.remove(temp_path)
    
    def test_load_nonexistent_file(self):
        """
        Test graceful handling of missing file.
        """
        contributions, author_exp = load_history_from_csv('nonexistent.csv')
        self.assertEqual(len(contributions), 0)
        self.assertEqual(len(author_exp), 0)

if __name__ == '__main__':
    unittest.main()
