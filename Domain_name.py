import whois

def get_domain_info(domain_name):
    try:
        # Query the domain information:
        domain = whois.whois(domain_name)
        print(f"Domain name: {domain.domain_name}")
        print(f"Registrar: {domain.registrar}")
        print(f"Creation date: {domain.creation_date}")
        print(f"Expiration date: {domain.expiration_date}")
        print(f"Name servers: {', '.join(domain.name_servers)}")
    except Exception as e:
        print(f"Error fetching information: {e}")

# Example usage:
if __name__ == "__main__":
    domain_name = input("Enter the domain name (e.g., example.com): ")
    get_domain_info(domain_name)