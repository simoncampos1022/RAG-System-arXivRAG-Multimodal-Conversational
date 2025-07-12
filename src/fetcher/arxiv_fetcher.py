import arxiv
import urllib.request
from pathlib  import Path
from dateutil import parser
from typing   import List, Dict, Any, Optional

from src.config import TEMP_DIR


class ArxivFetcher:
    def __init__(self):
        self.client = arxiv.Client()
    
    
    def fetch_papers(self, 
                     subject_tags: List[str] = None, 
                     start_date  : str       = None, 
                     end_date    : str       = None, 
                     max_results : int       = 10,
                     query       : str       = None) -> List[Dict[str, Any]]:
        """
        Fetches papers from arXiv based on subject tags and date range.
        
        Args:
            subject_tags (list): List of subject tags to filter papers by
            start_date    (str): Start date in YYYY-MM-DD format
            end_date      (str): End date in YYYY-MM-DD format
            query         (str): Search query for text-based search
            max_results   (int): Maximum number of results to return

        Returns:
            list: List of paper dictionaries with metadata
        """
        # Search query
        if not subject_tags: filter_query = 'cat:cs.*'                                          # Default to all CS tags
        else               : filter_query = ' OR '.join([f"cat:{tag}" for tag in subject_tags]) # Query with selected tags

        full_query = f'(ti:"{query}" OR abs:"{query}") AND ({filter_query})' if query else filter_query

        # Search object
        search = arxiv.Search(
            query       = full_query,
            max_results = max_results,
            sort_by     = arxiv.SortCriterion.SubmittedDate
        )
        
        try:
            results = list(self.client.results(search))
            
            # Filter by date
            if start_date or end_date:
                filtered_results = []
                start_date_obj   = parser.parse(start_date).date() if start_date else None
                end_date_obj     = parser.parse(end_date).date()   if end_date   else None
                
                for paper in results:
                    paper_date = paper.published.date()
                    if start_date_obj and paper_date < start_date_obj: continue
                    if end_date_obj   and paper_date > end_date_obj  : continue
                    
                    filtered_results.append(paper)
                
                results = filtered_results
            
            # Convert to dictionary format with required metadata
            papers = []
            for paper in results:
                papers.append({
                    'title'           : paper.title,
                    'authors'         : [author.name for author in paper.authors],
                    'published'       : paper.published.strftime('%Y-%m-%d'),
                    'updated'         : paper.updated.strftime('%Y-%m-%d') if paper.updated else None,
                    'arxiv_id'        : paper.get_short_id(),
                    'pdf_url'         : paper.pdf_url,
                    'entry_id'        : paper.entry_id,
                    'abstract'        : paper.summary,
                    'categories'      : paper.categories,
                    'primary_category': paper.primary_category
                })
            return papers
            
        except Exception as e:
            print(f"Error fetching papers: {e}")
            return []

    
    def download_paper(self, paper_id: str) -> Optional[Path]:
        """
        Downloads a paper's PDF from arXiv.
        
        Args:
            paper_id (str): The arXiv ID of the paper
            
        Returns:
            Optional[Path]: Path to the downloaded PDF file, or None if download failed
        """
        try:
            # Create the filename
            filename = f"{paper_id.replace('/', '_')}.pdf"
            filepath = TEMP_DIR / filename
            
            # Check if the file already exists
            if filepath.exists():
                return filepath
                
            # Construct the PDF URL
            pdf_url = f"https://arxiv.org/pdf/{paper_id}"
            
            # Download the PDF
            urllib.request.urlretrieve(pdf_url, filepath)
            
            return filepath
        
        except Exception as e:
            print(f"Error downloading paper {paper_id}: {e}")
            return None