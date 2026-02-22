"""
Web browsing tool using Playwright for human-like web navigation.
Enables the agent to browse websites, fill forms, and interact with web content.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

logger = logging.getLogger(__name__)

class WebBrowserTool:
    """
    Web browsing tool using Playwright.
    Provides human-like web navigation and interaction capabilities.
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize the web browser tool.
        
        Args:
            headless: Run browser in headless mode
            timeout: Page timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        logger.info("Web browser tool initialized")
    
    async def initialize(self):
        """Initialize the browser and context."""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.timeout)
            logger.info("Browser initialized")
        except Exception as e:
            logger.error(f"Error initializing browser: {str(e)}")
            raise
    
    async def close(self):
        """Close the browser."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
            
        Returns:
            Page information
        """
        try:
            if not self.page:
                await self.initialize()
            
            await self.page.goto(url, wait_until="networkidle")
            
            # Get page info
            title = await self.page.title()
            content = await self.page.content()
            
            logger.info(f"Navigated to {url}")
            
            return {
                "success": True,
                "url": self.page.url,
                "title": title,
                "content_length": len(content)
            }
        
        except Exception as e:
            logger.error(f"Error navigating to {url}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_page_content(self, selector: Optional[str] = None) -> str:
        """
        Get page content.
        
        Args:
            selector: Optional CSS selector to get specific content
            
        Returns:
            Page content as string
        """
        try:
            if not self.page:
                raise Exception("Browser not initialized")
            
            if selector:
                element = await self.page.query_selector(selector)
                if element:
                    return await element.inner_text()
                return ""
            else:
                return await self.page.content()
        
        except Exception as e:
            logger.error(f"Error getting page content: {str(e)}")
            return ""
    
    async def click(self, selector: str) -> Dict[str, Any]:
        """
        Click an element.
        
        Args:
            selector: CSS selector of element to click
            
        Returns:
            Click result
        """
        try:
            if not self.page:
                raise Exception("Browser not initialized")
            
            await self.page.click(selector)
            logger.info(f"Clicked element: {selector}")
            
            return {
                "success": True,
                "message": f"Clicked {selector}"
            }
        
        except Exception as e:
            logger.error(f"Error clicking {selector}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def fill_input(self, selector: str, text: str) -> Dict[str, Any]:
        """
        Fill an input field.
        
        Args:
            selector: CSS selector of input field
            text: Text to fill
            
        Returns:
            Fill result
        """
        try:
            if not self.page:
                raise Exception("Browser not initialized")
            
            await self.page.fill(selector, text)
            logger.info(f"Filled input {selector}")
            
            return {
                "success": True,
                "message": f"Filled {selector} with text"
            }
        
        except Exception as e:
            logger.error(f"Error filling input {selector}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def submit_form(self, selector: str) -> Dict[str, Any]:
        """
        Submit a form.
        
        Args:
            selector: CSS selector of form
            
        Returns:
            Submit result
        """
        try:
            if not self.page:
                raise Exception("Browser not initialized")
            
            await self.page.locator(selector).evaluate("form => form.submit()")
            await self.page.wait_for_load_state("networkidle")
            
            logger.info(f"Submitted form: {selector}")
            
            return {
                "success": True,
                "message": "Form submitted",
                "url": self.page.url
            }
        
        except Exception as e:
            logger.error(f"Error submitting form {selector}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def extract_links(self) -> List[Dict[str, str]]:
        """
        Extract all links from the page.
        
        Returns:
            List of links with text and href
        """
        try:
            if not self.page:
                raise Exception("Browser not initialized")
            
            links = await self.page.locator("a").all()
            result = []
            
            for link in links:
                href = await link.get_attribute("href")
                text = await link.inner_text()
                if href:
                    result.append({
                        "text": text.strip(),
                        "href": href
                    })
            
            logger.info(f"Extracted {len(result)} links")
            return result
        
        except Exception as e:
            logger.error(f"Error extracting links: {str(e)}")
            return []
    
    async def take_screenshot(self, path: str) -> Dict[str, Any]:
        """
        Take a screenshot of the page.
        
        Args:
            path: Path to save screenshot
            
        Returns:
            Screenshot result
        """
        try:
            if not self.page:
                raise Exception("Browser not initialized")
            
            await self.page.screenshot(path=path)
            logger.info(f"Screenshot saved to {path}")
            
            return {
                "success": True,
                "path": path
            }
        
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search(self, query: str, search_engine: str = "google") -> Dict[str, Any]:
        """
        Perform a web search.
        
        Args:
            query: Search query
            search_engine: Search engine to use (google, bing, duckduckgo)
            
        Returns:
            Search results
        """
        try:
            if not self.page:
                await self.initialize()
            
            # Build search URL
            if search_engine == "google":
                url = f"https://www.google.com/search?q={query}"
            elif search_engine == "bing":
                url = f"https://www.bing.com/search?q={query}"
            else:  # duckduckgo
                url = f"https://duckduckgo.com/?q={query}"
            
            await self.navigate(url)
            
            # Extract search results
            results = await self.extract_links()
            
            logger.info(f"Search completed for: {query}")
            
            return {
                "success": True,
                "query": query,
                "results": results[:10]  # Top 10 results
            }
        
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Global browser instance
_browser_tool: Optional[WebBrowserTool] = None

def get_browser_tool() -> WebBrowserTool:
    """Get or create the global browser tool."""
    global _browser_tool
    if _browser_tool is None:
        _browser_tool = WebBrowserTool()
    return _browser_tool

async def initialize_browser_tool():
    """Initialize the browser tool."""
    tool = get_browser_tool()
    await tool.initialize()
    return tool

async def close_browser_tool():
    """Close the browser tool."""
    global _browser_tool
    if _browser_tool:
        await _browser_tool.close()
        _browser_tool = None
