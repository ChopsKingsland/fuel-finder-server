import os
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

class OAuthManager:
    """
    Manages authentication with the Fuel Finder OAuth API.

    Handles retrieving, generating, and automatically refreshing access 
    and refresh tokens using credentials from the environment.
    """

    BASE_URL = "https://www.fuel-finder.service.gov.uk/api/v1/oauth"
    def __init__(self):
        """
        Initializes the OAuth manager and loads API credentials from environment variables.

        Raises:
            RuntimeError: If `FUEL_CLIENT_ID` or `FUEL_CLIENT_SECRET` are not set.
        """

        self.client_id = os.getenv("FUEL_CLIENT_ID")
        self.client_secret = os.getenv("FUEL_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise RuntimeError(
                "Missing FUEL_CLIENT_ID or FUEL_CLIENT_SECRET in .env"
            )

        self.access_token = None
        self.access_expiry = None

        self.refresh_token = None
        self.refresh_expiry = None


    def get_access_token(self):
        """
        Retrieves a valid access token, refreshing or regenerating it as necessary.

        Returns:
            str: A valid OAuth access token.
        """

        now = datetime.now(timezone.utc)

        # existing access token still valid
        if (
            self.access_token
            and self.access_expiry
            and now < self.access_expiry - timedelta(minutes=5)
        ):
            return self.access_token

        # try refresh token
        if (
            self.refresh_token
            and self.refresh_expiry
            and now < self.refresh_expiry - timedelta(minutes=5)
        ):
            try:
                self._refresh()
                return self.access_token

            except Exception as e:
                print(f"Refresh failed: {e}")

        # no usable token, generate a new one
        self._generate()

        return self.access_token

    def _generate(self):
        """
        Requests a new access and refresh token pair using the client credentials.

        Updates internal token stores and expiry timestamps.

        Raises:
            RuntimeError: If the API response indicates failure or HTTP error occurs.
        """

        print("Generating new OAuth token")

        response = requests.post(
            f"{self.BASE_URL}/generate_access_token",
            json={
                "client_id": self.client_id,
                "client_secret": self.client_secret
            },
            timeout=30
        )

        response.raise_for_status()

        body = response.json()

        if not body.get("success"):
            raise RuntimeError(body)

        data = body["data"]

        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]

        now = datetime.now(timezone.utc)

        self.access_expiry = now + timedelta(
            seconds=data["expires_in"]
        )

        self.refresh_expiry = now + timedelta(
            seconds=data["refresh_token_expires_in"]
        )

    def _refresh(self):
        """
        Refreshes the current access token using the active refresh token.

        Updates internal access token, optional rotated refresh token, and expiry timestamps.
        """

        print("Refreshing OAuth token")

        response = requests.post(
            f"{self.BASE_URL}/regenerate_access_token",
            json={
                "client_id": self.client_id,
                "refresh_token": self.refresh_token
            },
            timeout=30
        )

        response.raise_for_status()

        body = response.json()

        # API example has no data wrapper on refresh
        data = body.get("data", body)

        self.access_token = data["access_token"]

        now = datetime.now(timezone.utc)

        self.access_expiry = now + timedelta(
            seconds=data["expires_in"]
        )

        # if rotate refresh tokens
        if "refresh_token" in data:
            self.refresh_token = data["refresh_token"]

        if "refresh_token_expires_in" in data:
            self.refresh_expiry = now + timedelta(
                seconds=data["refresh_token_expires_in"]
            )


if __name__ == "__main__":
    oauth = OAuthManager()
    token = oauth.get_access_token()

    print("Access token:")
    print(token)