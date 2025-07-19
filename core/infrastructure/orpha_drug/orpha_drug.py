import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
from typing import Dict, List, Optional, Union
import logging
import re
import json

class DrugParser:
    """
    Handles HTML parsing of Orpha.net drug search results.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_search_results(self, soup: BeautifulSoup) -> Dict:
        """
        Parse complete search results from HTML.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Dictionary containing parsed data
        """
        try:
            results = {
                'drugs': self.parse_drugs(soup),
                'disease_info': self.parse_disease_info(soup),
                'total_results': self.parse_result_count(soup),
                'page_info': self.parse_page_info(soup)
            }
            
            self.logger.info(f"Parsed {len(results['drugs'])} drugs from search results")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to parse search results: {e}")
            return {'error': f"Parsing failed: {e}"}
    
    def parse_drugs(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse drug information from search results with specific vs non-specific classification."""
        drugs = []
        
        # Parse specific drugs (direct relation)
        specific_drugs = self._parse_specific_drugs(soup)
        drugs.extend(specific_drugs)
        
        # Parse non-specific drugs (parent relation) 
        non_specific_drugs = self._parse_non_specific_drugs(soup)
        drugs.extend(non_specific_drugs)
        
        # Deduplicate and merge similar drugs
        drugs = self._deduplicate_and_merge_drugs(drugs)
        
        return drugs
    
    def _parse_specific_drugs(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse drugs from the 'specific results' section."""
        drugs = []
        
        # Find the specific results section
        specific_section = soup.find('h3', id='direct-relation')
        if not specific_section:
            return drugs
        
        # Get all drug containers after the specific section header
        current = specific_section.find_next_sibling()
        while current and current.name != 'h3':
            drug_containers = current.find_all('div', class_='drug-card')
            for container in drug_containers:
                try:
                    drug_data = self._parse_single_drug_improved(container, is_specific=True)
                    if drug_data and drug_data.get('name'):
                        drugs.append(drug_data)
                except Exception as e:
                    self.logger.warning(f"Failed to parse specific drug: {e}")
                    continue
            current = current.find_next_sibling()
        
        return drugs
    
    def _parse_non_specific_drugs(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse drugs from the 'including the selected disease' section."""
        drugs = []
        
        # Find the parent relation section
        parent_section = soup.find('h3', id='parent-relation')
        if not parent_section:
            return drugs
        
        # Check if parent results are hidden (collapsed)
        parent_container = soup.find('div', class_='parent')
        if parent_container:
            drug_containers = parent_container.find_all('div', class_='drug-card')
            for container in drug_containers:
                try:
                    drug_data = self._parse_single_drug_improved(container, is_specific=False)
                    if drug_data and drug_data.get('name'):
                        drugs.append(drug_data)
                except Exception as e:
                    self.logger.warning(f"Failed to parse non-specific drug: {e}")
                    continue
        
        return drugs
    
    def _deduplicate_and_merge_drugs(self, drugs: List[Dict]) -> List[Dict]:
        """Deduplicate and merge drug records that represent the same drug in different regions."""
        if not drugs:
            return drugs
        
        # Create a dictionary to group drugs by name and substance_id
        drug_groups = {}
        
        for drug in drugs:
            # Create a key based on name and substance_id
            name = drug.get('name', '').strip()
            substance_id = drug.get('substance_id', '')
            
            # For drugs without substance_id, also check substance_url
            if not substance_id and drug.get('substance_url'):
                # Extract ID from substance URL
                url = drug.get('substance_url', '')
                if '/' in url:
                    # Extract the ID part from URLs like "/en/drug/substance/299541?..."
                    parts = url.split('/')
                    for i, part in enumerate(parts):
                        if part in ['substance', 'trade_name'] and i + 1 < len(parts):
                            id_part = parts[i + 1].split('?')[0]  # Remove query parameters
                            substance_id = id_part
                            break
            
            # Create a unique key for grouping
            key = f"{name}|{substance_id}"
            
            if key not in drug_groups:
                drug_groups[key] = []
            drug_groups[key].append(drug)
        
        # Merge drugs in each group
        merged_drugs = []
        for key, group in drug_groups.items():
            if len(group) == 1:
                # Single drug, no merging needed
                merged_drugs.append(group[0])
            else:
                # Multiple drugs with same name/substance_id, merge them
                merged_drug = self._merge_drug_group(group)
                merged_drugs.append(merged_drug)
                self.logger.info(f"Merged {len(group)} drug records for '{group[0].get('name', 'Unknown')}'")
        
        return merged_drugs
    
    def _merge_drug_group(self, drug_group: List[Dict]) -> Dict:
        """Merge a group of drug records that represent the same drug."""
        if not drug_group:
            return {}
        
        # Start with the first drug as base
        merged = drug_group[0].copy()
        
        # Merge boolean fields using OR logic (if any record has True, result is True)
        boolean_fields = ['is_tradename', 'is_medical_product', 'is_available_in_us', 'is_available_in_eu', 'is_specific']
        
        for field in boolean_fields:
            merged[field] = any(drug.get(field, False) for drug in drug_group)
        
        # For non-boolean fields, prefer non-null/non-empty values
        string_fields = ['name', 'substance_url', 'substance_id', 'regulatory_url', 'regulatory_id']
        
        for field in string_fields:
            # Find the first non-empty value for this field
            for drug in drug_group:
                value = drug.get(field)
                if value and str(value).strip():
                    merged[field] = value
                    break
        
        # For regulatory_url and regulatory_id, we might want to keep multiple values
        # But for simplicity, we'll keep the first non-empty one
        # In a more complex scenario, we could store all regulatory URLs as a list
        
        return merged
    
    def _parse_single_drug_improved(self, container, is_specific: bool) -> Dict:
        """Parse a single drug with the improved simplified schema."""
        drug_data = {
            'name': None,
            'substance_url': None,
            'substance_id': None,
            'regulatory_url': None,
            'regulatory_id': None,
            'is_tradename': False,
            'is_medical_product': False,
            'is_available_in_us': False,
            'is_available_in_eu': False,
            'is_specific': is_specific
        }
        
        # Extract drug name and URLs from the main drug link
        drug_link = None
        
        # Look for substance link first
        substance_link = container.find('a', href=lambda x: x and '/substance/' in x)
        if substance_link:
            drug_link = substance_link
            drug_data['substance_url'] = substance_link['href']
            drug_data['substance_id'] = self._extract_id_from_url(substance_link['href'], 'substance')
            drug_data['is_medical_product'] = True
        else:
            # Look for trade name link
            trade_link = container.find('a', href=lambda x: x and '/trade_name/' in x)
            if trade_link:
                drug_link = trade_link
                drug_data['substance_url'] = trade_link['href']
                drug_data['substance_id'] = self._extract_id_from_url(trade_link['href'], 'trade_name')
                drug_data['is_tradename'] = True
        
        # Extract drug name
        if drug_link:
            drug_data['name'] = drug_link.get_text(strip=True)
        
        # Extract regulatory URL
        regulatory_link = container.find('a', href=lambda x: x and '/regulatory/' in x)
        if regulatory_link:
            drug_data['regulatory_url'] = regulatory_link['href']
            drug_data['regulatory_id'] = self._extract_id_from_url(regulatory_link['href'], 'regulatory')
        
        # Determine drug type from text content
        container_text = container.get_text().lower()
        
        # Check if it's explicitly a medicinal product (overrides the URL-based detection)
        if 'medicinal product' in container_text:
            drug_data['is_medical_product'] = True
            drug_data['is_tradename'] = False
        elif 'tradename' in container_text:
            drug_data['is_tradename'] = True
            drug_data['is_medical_product'] = False
        
        # Determine regional availability based on the section headers
        # The structure is: <div class="h2 text-black">Europe</div> or <div class="h2 text-black">USA</div>
        # followed by the drug containers
        
        # Find the closest preceding regional header
        current_element = container
        region_found = False
        
        # Look through all preceding elements to find the most recent regional header
        all_preceding = []
        temp_element = container
        while temp_element:
            for prev_sibling in temp_element.find_all_previous():
                all_preceding.append(prev_sibling)
            temp_element = temp_element.parent
        
        # Search through preceding elements for regional headers
        for element in all_preceding:
            if (hasattr(element, 'get') and 
                element.name == 'div' and 
                'h2' in element.get('class', []) and 
                'text-black' in element.get('class', [])):
                
                region_text = element.get_text(strip=True).lower()
                if region_text == 'europe':
                    drug_data['is_available_in_eu'] = True
                    region_found = True
                    break
                elif region_text == 'usa':
                    drug_data['is_available_in_us'] = True
                    region_found = True
                    break
        
        # If we didn't find a region header, this might be a parsing issue
        # In that case, we'll leave both flags as False rather than guess
        
        return drug_data
    
    def _parse_single_drug(self, container) -> Dict:
        """Parse a single drug from its container."""
        drug_data = {}
        
        # Extract drug name
        drug_data['name'] = self._extract_drug_name(container)
        
        # Extract substance information
        substance_info = self._extract_substance_info(container)
        drug_data.update(substance_info)
        
        # Extract drug details
        drug_data['details'] = self._extract_drug_details(container)
        
        # Extract links
        drug_data['links'] = self._extract_drug_links(container)
        
        # Extract status/approval info
        drug_data['status'] = self._extract_drug_status(container)
        
        # Extract manufacturer
        drug_data['manufacturer'] = self._extract_manufacturer(container)
        
        # Extract indication/disease
        drug_data['indication'] = self._extract_indication(container)
        
        # Extract region/country info
        drug_data['regions'] = self._extract_regions(container)
        
        return drug_data
    
    def _extract_drug_name(self, container) -> Optional[str]:
        """Extract drug name from container."""
        # Strategy 1: Look for substance links (Orpha.net specific)
        substance_links = container.find_all('a', href=lambda x: x and 'substance' in x)
        for link in substance_links:
            name = link.get_text(strip=True)
            if name and len(name) > 1:
                return name
        
        # Strategy 2: Look for trade name links
        trade_links = container.find_all('a', href=lambda x: x and 'trade_name' in x)
        for link in trade_links:
            name = link.get_text(strip=True)
            if name and len(name) > 1:
                return name
        
        # Strategy 3: Try standard selectors
        name_selectors = [
            'h3', 'h4', 'h5',
            '.drug-name', '.substance-name', '.medication-name',
            'a[href*="drug"]',
            'td:first-child', 'strong', '.title'
        ]
        
        for selector in name_selectors:
            elements = container.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 1 and not text.isdigit():
                    return text
        
        return None
    
    def _extract_substance_info(self, container) -> Dict:
        """Extract substance URL and ID information."""
        substance_info = {
            'substance_url': None,
            'substance_id': None,
            'regulatory_url': None,
            'regulatory_id': None,
            'orpha_substance_code': None
        }
        
        # Look for substance and regulatory links
        all_links = container.find_all('a', href=True)
        for link in all_links:
            href = link['href']
            
            # Check if it's a substance URL
            if '/substance/' in href:
                substance_info['substance_url'] = href
                # Extract substance ID from URL like /en/drug/substance/696848
                substance_id = self._extract_id_from_url(href, 'substance')
                if substance_id:
                    substance_info['substance_id'] = substance_id
            
            # Check if it's a regulatory URL  
            elif '/regulatory/' in href:
                substance_info['regulatory_url'] = href
                # Extract regulatory ID from URL like /en/drug/regulatory/696873
                regulatory_id = self._extract_id_from_url(href, 'regulatory')
                if regulatory_id:
                    substance_info['regulatory_id'] = regulatory_id
            
            # Look for ORPHA substance codes
            link_text = link.get_text(strip=True)
            if 'ORPHA:' in link_text:
                import re
                orpha_match = re.search(r'ORPHA:(\d+)', link_text)
                if orpha_match:
                    substance_info['orpha_substance_code'] = f"ORPHA:{orpha_match.group(1)}"
        
        # Also check for substance info in data attributes
        for attr in ['data-substance-id', 'data-substance-code', 'data-id']:
            if container.get(attr):
                substance_info['substance_id'] = container.get(attr)
                break
        
        return substance_info
    
    def _extract_id_from_url(self, url: str, param_name: str) -> Optional[str]:
        """Extract ID parameter from URL."""
        try:
            # For Orpha.net URLs like /en/drug/substance/696848 or /en/drug/regulatory/696873
            if f'/{param_name}/' in url:
                import re
                # Extract the ID after /substance/ or /regulatory/
                pattern = rf'/{param_name}/(\d+)'
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            # Parse URL parameters as fallback
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            
            # Look for various ID parameters
            id_params = [param_name + 'Id', param_name + 'Code', 'id', 'code']
            
            for param in id_params:
                if param in params and params[param]:
                    return params[param][0]
            
            # Try to extract from path (general pattern)
            path_match = re.search(rf'{param_name}/(\d+)', url)
            if path_match:
                return path_match.group(1)
            
        except Exception as e:
            self.logger.warning(f"Failed to extract ID from URL {url}: {e}")
        
        return None
    
    def _extract_drug_details(self, container) -> List[str]:
        """Extract detailed drug information."""
        details = []
        
        # Get all table cells
        cells = container.find_all('td')
        for cell in cells:
            text = cell.get_text(strip=True)
            if text and len(text) > 2:
                details.append(text)
        
        # Get spans and divs with meaningful content
        for element in container.find_all(['span', 'div', 'p']):
            text = element.get_text(strip=True)
            if text and len(text) > 5 and text not in details:
                details.append(text)
        
        return details
    
    def _extract_drug_links(self, container) -> List[Dict]:
        """Extract all links related to the drug."""
        links = []
        
        for link in container.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            # Categorize link type
            link_type = self._categorize_link(href, text)
            
            # Make URL absolute if needed
            if href.startswith('/'):
                href = f"https://www.orpha.net{href}"
            
            links.append({
                'url': href,
                'text': text,
                'type': link_type
            })
        
        return links
    
    def _categorize_link(self, href: str, text: str) -> str:
        """Categorize the type of link."""
        href_lower = href.lower()
        text_lower = text.lower()
        
        if '/substance/' in href_lower:
            return 'substance_details'
        elif '/regulatory/' in href_lower:
            return 'regulatory_status'
        elif '/trade_name/' in href_lower:
            return 'trade_name_details'
        elif '/disease/detail/' in href_lower:
            return 'disease_details'
        elif 'drug' in href_lower and 'substance' not in href_lower:
            return 'drug_details'
        elif 'pdf' in href_lower or '.pdf' in href_lower:
            return 'pdf_document'
        elif any(domain in href_lower for domain in ['pubmed', 'ncbi']):
            return 'pubmed_reference'
        elif 'clinicaltrials.gov' in href_lower:
            return 'clinical_trial'
        elif any(domain in href_lower for domain in ['ema.europa.eu', 'fda.gov']):
            return 'regulatory_agency'
        elif 'details' in text_lower or 'more' in text_lower:
            return 'details'
        elif 'regulatory status' in text_lower:
            return 'regulatory_status'
        else:
            return 'other'
    
    def _extract_drug_status(self, container) -> Optional[str]:
        """Extract drug approval/status information."""
        # Strategy 1: Look for Orpha.net specific status format "(Medicinal product - date)"
        all_text = container.get_text()
        status_patterns = [
            r'\((Medicinal product)\s*-\s*[\d/]+\)',
            r'\((Tradename)\s*-\s*[\d/]+\)',
            r'\((.*?)\s*-\s*[\d/]+\)'  # Generic pattern for any status with date
        ]
        
        for pattern in status_patterns:
            import re
            matches = re.findall(pattern, all_text)
            if matches:
                return matches[0].strip()
        
        # Strategy 2: Look for status indicators in specific elements
        status_elements = container.find_all(['span', 'div', 'td'], 
                                           class_=['status', 'approval', 'regulatory'])
        
        for element in status_elements:
            text = element.get_text(strip=True).lower()
            if any(keyword in text for keyword in ['approved', 'investigational', 'withdrawn', 'authorized']):
                return text.title()
        
        # Strategy 3: Look for section headers that indicate status type
        section_headers = container.find_previous(['h4', 'h3', 'h2'])
        if section_headers:
            header_text = section_headers.get_text().lower()
            if 'marketing authorisation' in header_text:
                return 'Marketing Authorisation'
            elif 'orphan designation' in header_text:
                return 'Orphan Designation'
            elif 'withdrawn' in header_text or 'expired' in header_text:
                return 'Withdrawn/Expired'
        
        # Strategy 4: Check all text for status keywords
        all_text_lower = all_text.lower()
        if 'approved' in all_text_lower:
            return 'Approved'
        elif 'investigational' in all_text_lower or 'clinical trial' in all_text_lower:
            return 'Investigational'
        elif 'withdrawn' in all_text_lower:
            return 'Withdrawn'
        
        return None
    
    def _extract_manufacturer(self, container) -> Optional[str]:
        """Extract manufacturer/company information."""
        # Look for company indicators
        text = container.get_text()
        
        # Common company suffixes
        company_patterns = [
            r'([A-Z][a-zA-Z\s&]+(?:Inc\.?|Ltd\.?|Corp\.?|LLC|GmbH|Pharmaceuticals|Pharma|Biotech))',
            r'([A-Z][a-zA-Z\s&]+(?:Company|Industries|Labs|Laboratories))'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0].strip()
        
        return None
    
    def _extract_indication(self, container) -> Optional[str]:
        """Extract indication/disease information."""
        # Look for indication in text
        text = container.get_text()
        
        # Common indication patterns
        indication_patterns = [
            r'indication[:\s]+([^\.]+)',
            r'disease[:\s]+([^\.]+)',
            r'syndrome[:\s]+([^\.]+)',
            r'disorder[:\s]+([^\.]+)'
        ]
        
        for pattern in indication_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return None
    
    def _extract_regions(self, container) -> List[str]:
        """Extract geographical regions where drug is available."""
        regions = []
        text = container.get_text().lower()
        
        # Common region indicators
        region_keywords = {
            'united states': 'US',
            'usa': 'US', 
            'us': 'US',
            'europe': 'EU',
            'european union': 'EU',
            'eu': 'EU',
            'japan': 'Japan',
            'canada': 'Canada',
            'australia': 'Australia'
        }
        
        for keyword, region in region_keywords.items():
            if keyword in text and region not in regions:
                regions.append(region)
        
        return regions
    
    def parse_disease_info(self, soup: BeautifulSoup) -> Dict:
        """Parse disease information from the page."""
        disease_info = {}
        
        try:
            # Extract disease name from title or headers
            disease_name = self._extract_disease_name(soup)
            if disease_name:
                disease_info['name'] = disease_name
            
            # Extract orphan code
            orphan_code = self._extract_orphan_code(soup)
            if orphan_code:
                disease_info['orphan_code'] = orphan_code
            
            # Extract disease description
            description = self._extract_disease_description(soup)
            if description:
                disease_info['description'] = description
            
        except Exception as e:
            self.logger.warning(f"Failed to parse disease info: {e}")
        
        return disease_info
    
    def _extract_disease_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract disease name from page."""
        # Try page title first
        title_elem = soup.find('title')
        if title_elem:
            title = title_elem.get_text()
            # Extract disease name from title
            if 'drug' in title.lower():
                # Try to extract disease name before "drug"
                parts = title.split('-')
                for part in parts:
                    if 'drug' not in part.lower() and len(part.strip()) > 3:
                        return part.strip()
        
        # Try headers
        for header in soup.find_all(['h1', 'h2', 'h3']):
            text = header.get_text(strip=True)
            if text and 'drug' not in text.lower() and len(text) > 3:
                return text
        
        return None
    
    def _extract_orphan_code(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract orphan code from page."""
        page_text = soup.get_text()
        
        # Look for ORPHA codes
        orpha_matches = re.findall(r'ORPHA[:\s]*(\d+)', page_text, re.IGNORECASE)
        if orpha_matches:
            return f"ORPHA:{orpha_matches[0]}"
        
        # Look in URL parameters
        url_text = str(soup)
        orphan_matches = re.findall(r'orphaCode[=:]\s*(\d+)', url_text, re.IGNORECASE)
        if orphan_matches:
            return f"ORPHA:{orphan_matches[0]}"
        
        return None
    
    def _extract_disease_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract disease description if available."""
        # Look for description paragraphs
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if len(text) > 100 and any(keyword in text.lower() 
                                     for keyword in ['syndrome', 'disorder', 'disease', 'condition']):
                return text[:500]  # Limit length
        
        return None
    
    def parse_result_count(self, soup: BeautifulSoup) -> Optional[int]:
        """Parse total number of results."""
        page_text = soup.get_text()
        
        # Common result count patterns
        patterns = [
            r'(\d+)\s+results?\s+found',
            r'(\d+)\s+drugs?\s+found',
            r'(\d+)\s+substances?\s+found',
            r'total[:\s]+(\d+)',
            r'(\d+)\s+of\s+\d+'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                try:
                    return int(matches[0])
                except ValueError:
                    continue
        
        return None
    
    def parse_page_info(self, soup: BeautifulSoup) -> Dict:
        """Parse general page information."""
        info = {}
        
        # Extract page title
        title_elem = soup.find('title')
        if title_elem:
            info['page_title'] = title_elem.get_text(strip=True)
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            info['meta_description'] = meta_desc.get('content', '')
        
        # Check if there are pagination elements
        pagination = soup.find_all(['nav', 'div'], class_=['pagination', 'pager'])
        info['has_pagination'] = len(pagination) > 0
        
        return info


class OrphaDrugAPIClient:
    """
    Handles API requests and searches for Orpha.net drug database.
    """
    
    def __init__(self, delay: float = 1.0):
        """
        Initialize the API client.
        
        Args:
            delay: Delay between requests in seconds
        """
        self.base_url = "https://www.orpha.net/en/drug"
        self.session = requests.Session()
        self.delay = delay
        self.parser = DrugParser()
        
        # Set respectful user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Track last request time for rate limiting
        self.last_request_time = 0
    
    def search(self, disease_name: str, orphacode: Union[str, int],
               region: str = "", status: str = "all") -> Dict:
        """
        Search for drugs using disease name and orphan code.
        
        Args:
            disease_name: Name of the disease
            orphacode: The orphan code number
            region: Geographic region filter (optional)
            status: Drug status filter (default: "all")
            
        Returns:
            Dictionary containing search results
        """
        params = {
            'diseaseName': disease_name,
            'orphaCode': str(orphacode),
            'name': str(orphacode),
            'region': region,
            'mode': 'orpha',
            'status': status
        }
        
        return self._execute_search(params)
    
    def _execute_search(self, params: Dict) -> Dict:
        """
        Execute search with given parameters.
        
        Args:
            params: URL parameters for the search
            
        Returns:
            Dictionary containing results or error information
        """
        try:
            # Respect rate limiting
            self._enforce_rate_limit()
            
            # Make the request
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Use parser to extract data
            parsed_results = self.parser.parse_search_results(soup)
            
            # Add metadata
            results = {
                'url': response.url,
                'search_params': params,
                'status_code': response.status_code,
                'timestamp': time.time(),
                **parsed_results
            }
            
            self.logger.info(f"Search completed successfully. Found {len(results.get('drugs', []))} drugs")
            return results
            
        except requests.RequestException as e:
            error_msg = f"Request failed: {e}"
            self.logger.error(error_msg)
            return {
                'error': error_msg,
                'search_params': params,
                'timestamp': time.time()
            }
        except Exception as e:
            error_msg = f"Search execution failed: {e}"
            self.logger.error(error_msg)
            return {
                'error': error_msg,
                'search_params': params,
                'timestamp': time.time()
            }
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.delay:
            sleep_time = self.delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_substance_details(self, substance_url: str) -> Dict:
        """
        Get detailed information about a specific substance.
        
        Args:
            substance_url: URL to the substance page
            
        Returns:
            Dictionary containing substance details
        """
        try:
            self._enforce_rate_limit()
            
            # Make sure URL is absolute
            if substance_url.startswith('/'):
                substance_url = f"https://www.orpha.net{substance_url}"
            
            response = self.session.get(substance_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse substance-specific information
            substance_details = self.parser.parse_search_results(soup)
            substance_details['substance_url'] = substance_url
            
            return substance_details
            
        except Exception as e:
            self.logger.error(f"Failed to get substance details from {substance_url}: {e}")
            return {'error': f"Failed to get substance details: {e}"}
    
    def save_results(self, results: Dict, filename: str):
        """Save search results to JSON file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Results saved to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save results to {filename}: {e}")


# Example usage
if __name__ == "__main__":
    # Initialize the API client
    client = OrphaDrugAPIClient(delay=1.5)
    
    # Search for Rett syndrome drugs
    print("=== Searching for Rett Syndrome Drugs ===")
    results = client.search(disease_name="Rett syndrome", orphacode=778)
    
    if 'drugs' in results:
        print(f"Found {len(results['drugs'])} drugs")
        
        # Show first few drugs with details
        for i, drug in enumerate(results['drugs'][:3], 1):
            print(f"\n--- Drug {i} ---")
            print(f"Name: {drug['name']}")
            print(f"Status: {drug.get('status', 'Unknown')}")
            print(f"Manufacturer: {drug.get('manufacturer', 'Unknown')}")
            print(f"Substance URL: {drug.get('substance_url', 'None')}")
            print(f"Substance ID: {drug.get('substance_id', 'None')}")
            print(f"Regulatory URL: {drug.get('regulatory_url', 'None')}")
            print(f"Regulatory ID: {drug.get('regulatory_id', 'None')}")
            
            # Show link types
            links = drug.get('links', [])
            if links:
                print(f"Available links ({len(links)}):")
                for link in links[:2]:  # Show first 2 links
                    print(f"  - {link['type']}: {link['text']}")
    
    # Test with different parameters
    print("\n=== Search with Region Filter ===")
    results_eu = client.search(disease_name="Rett syndrome", orphacode=778, region="Europe")
    if 'drugs' in results_eu:
        print(f"Found {len(results_eu['drugs'])} drugs in Europe")
    
    print("\n=== Search with Status Filter ===") 
    results_approved = client.search(disease_name="Rett syndrome", orphacode=778, status="mrk")
    if 'drugs' in results_approved:
        print(f"Found {len(results_approved['drugs'])} drugs with marketing authorization")
    
    # Save results
    client.save_results(results, "orpha_rett_syndrome.json")
    
    # Get substance details if available
    if results.get('drugs') and results['drugs'][0].get('substance_url'):
        print("\n=== Getting Substance Details ===")
        substance_url = results['drugs'][0]['substance_url']
        substance_details = client.get_substance_details(substance_url)
        print(f"Substance details retrieved: {len(substance_details.get('drugs', []))} items")
    
    # Show results summary
    if 'drugs' in results:
        print(f"\n=== SUMMARY ===")
        print(f"Total drugs found: {len(results['drugs'])}")
        print(f"Disease: {results.get('disease_info', {}).get('name', 'Unknown')}")
        print(f"Orphan code: {results.get('disease_info', {}).get('orphan_code', 'Unknown')}")
        
        # Count by status
        status_counts = {}
        for drug in results['drugs']:
            status = drug.get('status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("Status breakdown:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
        
        # Count substances with IDs
        with_substance_id = sum(1 for drug in results['drugs'] if drug.get('substance_id'))
        print(f"Drugs with substance IDs: {with_substance_id}")
        
        # Count regulatory links
        with_regulatory = sum(1 for drug in results['drugs'] if drug.get('regulatory_url'))
        print(f"Drugs with regulatory links: {with_regulatory}")
    
    # Example of other diseases
    print(f"\n=== Other Disease Examples ===")
    other_diseases = [
        {"name": "Huntington disease", "code": 399},
        {"name": "Cystic fibrosis", "code": 586}
    ]
    
    for disease in other_diseases:
        print(f"To search {disease['name']}: client.search(disease_name='{disease['name']}', orphacode={disease['code']})")

