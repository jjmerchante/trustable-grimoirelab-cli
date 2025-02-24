import json
import unittest

from trustable_cli.metrics import GitEventsAnalyzer


def read_file(filename):
    with open(filename) as f:
        return f.read()


class TestGitEventsAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = GitEventsAnalyzer()
        self.events = json.loads(read_file("data/events.json"))

    def test_commit_count(self):
        """Test that the commit count is calculated correctly"""

        self.analyzer.process_events(self.events)
        self.assertEqual(self.analyzer.get_commit_count(), 9)

    def test_contributor_count(self):
        """Test that the contributor count is calculated correctly"""

        self.analyzer.process_events(self.events)
        self.assertEqual(self.analyzer.get_contributor_count(), 3)

        extra_events = [
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            }
        ]
        self.analyzer.process_events(extra_events)
        self.assertEqual(self.analyzer.get_contributor_count(), 4)

    def test_get_pony_factor(self):
        """Test the computation of the pony factor is correct"""

        self.assertEqual(self.analyzer.get_pony_factor(), 0)

        self.analyzer.process_events(self.events)
        self.assertEqual(self.analyzer.get_pony_factor(), 1)

        # Include commits from another author to increase the pony factor
        extra_events = [
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            },
        ]
        self.analyzer.process_events(extra_events)
        self.assertEqual(self.analyzer.get_pony_factor(), 2)

    def test_get_elephant_factor(self):
        """Test the computation of the elephant factor is correct"""

        self.assertEqual(self.analyzer.get_elephant_factor(), 0)

        self.analyzer.process_events(self.events)
        self.assertEqual(self.analyzer.get_elephant_factor(), 1)

        # Include commits from another company to increase the elephant factor.
        extra_events = [
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example2.com>", "message": "Another commit"},
            },
        ]
        self.analyzer.process_events(extra_events)
        self.assertEqual(self.analyzer.get_elephant_factor(), 2)

    def test_file_type_metrics(self):
        """Test that file type metrics are calculated correctly"""

        self.assertEqual(self.analyzer.get_file_type_metrics(), {})

        self.analyzer.process_events(self.events)

        file_metrics = self.analyzer.get_file_type_metrics()
        self.assertEqual(file_metrics.get("Code", 0), 54)
        self.assertEqual(file_metrics.get("Other", 0), 24)

    def test_commit_size_metrics(self):
        """Test that commit size metrics are calculated correctly"""

        self.assertEqual(self.analyzer.get_commit_size_metrics(), {"added_lines": 0, "removed_lines": 0})

        self.analyzer.process_events(self.events)

        commit_size = self.analyzer.get_commit_size_metrics()
        self.assertEqual(commit_size["added_lines"], 5352)
        self.assertEqual(commit_size["removed_lines"], 562)

    def test_message_size_metrics(self):
        """Test that message size metrics are calculated correctly"""

        self.analyzer.process_events(self.events)

        metrics = self.analyzer.get_message_size_metrics()
        self.assertEqual(metrics["total"], 1891)
        self.assertAlmostEqual(metrics["average"], 210.11, delta=0.1)
        self.assertEqual(metrics["median"], 229)

    def test_get_average_commits_week(self):
        """Test whether the average commits per week is calculated correctly"""

        self.analyzer.process_events(self.events)
        avg = self.analyzer.get_average_commits_week(days_interval=30)
        self.assertAlmostEqual(avg, 9 / 30 / 7, delta=0.1)

    def test_get_developer_categories(self):
        """Test if the developer categories are calculated correctly"""

        categories = self.analyzer.get_developer_categories()
        self.assertDictEqual(categories, {"core": 0, "regular": 0, "casual": 0})

        self.analyzer.process_events(self.events)
        categories = self.analyzer.get_developer_categories()
        self.assertDictEqual(categories, {"core": 1, "regular": 1, "casual": 1})

        # Add a core developer to change the categories
        extra_events = [
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example_new.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example_new.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example_new.com>", "message": "Another commit"},
            },
            {
                "type": "org.grimoirelab.events.git.commit",
                "data": {"Author": "Author 1 <author1@example_new.com>", "message": "Another commit"},
            },
        ]

        self.analyzer.process_events(extra_events)
        categories = self.analyzer.get_developer_categories()
        self.assertDictEqual(categories, {"core": 2, "regular": 1, "casual": 1})


if __name__ == "__main__":
    unittest.main()
