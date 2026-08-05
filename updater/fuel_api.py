import requests, time
from updater.oauth import OAuthManager

class FuelFinderAPI:
    BASE_URL = "https://www.fuel-finder.service.gov.uk/api/v1"

    def __init__(self, oauth):
        self.oauth = oauth
        self.session = requests.Session()
    
    def get(self, endpoint, params=None):
        token = self.oauth.get_access_token()

        response = self.session.get(
            f"{self.BASE_URL}{endpoint}",
            headers={
                "Authorization": f"Bearer {token}"
            },
            params=params,
            timeout=30
        )

        # token expired unexpectedly
        if response.status_code == 401:
            print("Token rejected, retrying with new token")

            # foarce OAuth to get a new token
            self.oauth.access_token = None

            token = self.oauth.get_access_token()

            response = self.session.get(
                f"{self.BASE_URL}{endpoint}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                params=params,
                timeout=30
            )

        response.raise_for_status()
        return response.json()
    
    def get_all_pages(
        self,
        endpoint,
        params=None
    ):
        results = []
        batch = 1
        
        print(f"Starting download of {endpoint}")

        while True:
            print(f"Downloading batch {batch}")
            
            request_params = {
                "batch-number": batch
            }
            
            if params:
                request_params.update(params)
            
            data = self.get(
                endpoint,
                params=request_params
            )
            
            results.extend(data)

            print(
                f"Received {len(data)} records"
            )

            if len(data) < 500:
                break

            batch += 1
            
            # gets around 30req/min
            time.sleep(4)

        return results


if __name__ == "__main__":
    oauth = OAuthManager()
    ff = FuelFinderAPI(oauth)
    
    res = ff.get_all_pages("/pfs")
    
    print(res)