#!/usr/bin/env python3
"""Define classes for testing functions"""
import unittest
from unittest.mock import patch, PropertyMock, Mock
from parameterized import parameterized, parameterized_class
from client import GithubOrgClient
from fixtures import TEST_PAYLOAD


class TestGithubOrgClient(unittest.TestCase):
    """defines test for GithubOrgClient"""
    @parameterized.expand([
        ("google",),
        ("abc",),
    ])
    @patch('client.get_json')
    def test_org(self, org_name, mock_get_json):
        """mocking get_json to avoid making actual HTTP calls"""
        expected_url = f"https://api.github.com/orgs/{org_name}"
        mock_get_json.return_value = {}
        client = GithubOrgClient(org_name)
        result = client.org
        mock_get_json.assert_called_once_with(expected_url)
        self.assertEqual(result, {})

    def test_public_repos_url(self):
        """testing _public_repos_url"""
        known_payload = {"repos_url": "https://api.github.com/orgs/ex/repos"}
        with patch('client.GithubOrgClient.org') as mock_org:
            mock_org.return_value = known_payload
            client = GithubOrgClient("ex")
            with patch.object(GithubOrgClient, '_public_repos_url',
                              new_callable=PropertyMock) as mock_p:
                mock_p.return_value = known_payload["repos_url"]
                result = client._public_repos_url
                expected_url = known_payload["repos_url"]
                self.assertEqual(result, expected_url)

    @patch('client.get_json')
    @patch('client.GithubOrgClient._public_repos_url',
           new_callable=PropertyMock)
    def test_public_repos(self, mock_pb_repos_url, mock_get_json):
        """test the public_repos method"""
        payload = [
            {"name": "repo1"},
            {"name": "repo2"},
            {"name": "repo3"},
            {"name": "repo4"},
        ]
        mock_pb_repos_url.return_value = "https://api.github.com/orgs/ex/repos"
        mock_get_json.return_value = payload
        client = GithubOrgClient("ex")
        repos = client.public_repos()
        mock_get_json.assert_called_once()
        mock_pb_repos_url.assert_called_once()
        expected_repos = [repo['name'] for repo in payload]
        self.assertEqual(repos, expected_repos)

    @parameterized.expand([
        ({"license": {"key": "my_license"}}, "my_license", True),
        ({"license": {"key": "other_license"}}, "my_license", False),
    ])
    def test_has_license(self, repo, license_key, expected_result):
        """test the has_license method"""
        client = GithubOrgClient("example")
        result = client.has_license(repo, license_key)
        self.assertEqual(result, expected_result)


@parameterized_class(
    ('org_payload', 'repos_payload', 'expected_repos', 'apache2_repos'),
    TEST_PAYLOAD
)
class TestIntegrationGithubOrgClient(unittest.TestCase):
    """Integration testing"""
    @classmethod
    def setUpClass(cls):
        """ prepare for testing """
        cls.org_mock = Mock()
        cls.org_mock.json = Mock(return_value=cls.org_payload)
        cls.repos_mock = Mock()
        cls.repos_mock.json = Mock(return_value=cls.repos_payload)
        cls.get_patcher = patch('requests.get')
        cls.get = cls.get_patcher.start()

        def side_effect_for_get(url):
            return options.get(url, cls.org_mock)

        options = {cls.org_payload["repos_url"]: cls.repos_mock}
        cls.get.side_effect = side_effect_for_get

    @classmethod
    def tearDownClass(cls):
        """stops the patcher"""
        cls.get_patcher.stop()

    def test_public_repos_integration(self):
        """Test public repos method"""
        y = GithubOrgClient("x")

        self.assertEqual(y.org, self.org_payload)
        self.assertEqual(y.repos_payload, self.repos_payload)

    def test_public_repos_with_license(self):
        """Test public repos method with license argument"""
        # Create a GithubOrgClient instance
        client = GithubOrgClient("example_organization")

        self.assertEqual(client.org, self.org_payload)
        self.assertEqual(client.repos_payload, self.repos_payload)

        self.assertEqual(client.public_repos(license="apache-2.0"),
                         self.apache2_repos)
