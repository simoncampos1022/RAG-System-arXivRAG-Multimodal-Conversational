import arxiv
from dateutil import parser

class ArxivFetcher:
    def __init__(self):
        self.client = arxiv.Client()
    
    
    def fetch_papers(self, subject_tags, start_date=None, end_date=None, max_results=100):
        """
        Fetches papers from arXiv based on subject tags and date range.
        
        Args:
            subject_tags (list): List of subject tags to filter papers by
            start_date (str)   : Start date in YYYY-MM-DD format
            end_date (str)     : End date in YYYY-MM-DD format
            max_results (int)  : Maximum number of results to return

        Returns:
            list: List of paper dictionaries with metadata
        """
        # Search query for arXiv API
        if not subject_tags:
            query = "cat:cs.*" # Default to all CS tags if none are selected
        else:
            query = " OR ".join([f"cat:{tag}" for tag in subject_tags]) # Create query with selected tags
            
        # Search object
        search = arxiv.Search(
            query       = query,
            max_results = max_results,
            sort_by     = arxiv.SortCriterion.SubmittedDate
        )
        
        try:
            results = list(self.client.results(search))
            
            # Filter by date (if specified)
            if start_date or end_date:
                filtered_results = []
                start_date_obj   = parser.parse(start_date).date() if start_date else None
                end_date_obj     = parser.parse(end_date).date()   if end_date   else None
                
                for paper in results:
                    paper_date = paper.published.date()
                    if start_date_obj and paper_date < start_date_obj:
                        continue
                    if end_date_obj and paper_date > end_date_obj:
                        continue
                    
                    filtered_results.append(paper)
                
                results = filtered_results
            
            # Convert to dictionary format with required metadata
            papers = []
            for paper in results:
                papers.append({
                    'title'     : paper.title,
                    'authors'   : [author.name for author in paper.authors],
                    'published' : paper.published.strftime('%d/%m/%Y'),
                    'link'      : paper.entry_id,
                    'abstract'  : paper.summary,
                    'categories': paper.categories
                })
            
            return papers
            
        except Exception as e:
            print(f"Error fetching papers: {e}")
            return []