"""
Production-grade Web Browsing Tool using Playwright and BeautifulSoup.
Implements Phase 1.2 of the Production Roadmap.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class WebBrowserTool:
    """
    Advanced web browser tool for navigation, content extraction, and interaction.
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._playwright = None

    async def initialize(self):
        """Initialize the browser and context."""
        if not self.browser:
            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.timeout)
            logger.info("Production browser initialized")

    async def navigate(self, url: str, wait_until: str = "networkidle") -> Dict[str, Any]:
        """Navigate to a URL and return page status."""
        try:
            await self.initialize()
            response = await self.page.goto(url, wait_until=wait_until, timeout=self.timeout)
            return {
                "success": True,
                "url": self.page.url,
                "status": response.status if response else 200,
                "title": await self.page.title()
            }
        except Exception as e:
            logger.error(f"Navigation error to {url}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def extract_content(self) -> Dict[str, Any]:
        """Extract text, links, and metadata from the current page using BeautifulSoup."""
        try:
            if not self.page:
                return {"success": False, "error": "No page loaded"}
            
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text(separator=' ', strip=True)
            links = []
            for a in soup.find_all('a', href=True):
                link_text = a.get_text(strip=True)
                href = a.get('href')
                if link_text and href and not href.startswith('javascript:'):
                    links.append({"text": link_text, "url": href})
            
            return {
                "success": True,
                "text": text[:15000], # Increased limit for production
                "links": links[:100],  # Increased limit
                "metadata": {
                    "title": await self.page.title(),
                    "url": self.page.url
                }
            }
        except Exception as e:
            logger.error(f"Extraction error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def click(self, selector: str) -> Dict[str, Any]:
        """Click an element."""
        try:
            if not self.page: raise Exception("Browser not initialized")
            await self.page.click(selector)
            return {"success": True, "message": f"Clicked {selector}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def fill_input(self, selector: str, text: str) -> Dict[str, Any]:
        """Fill an input field."""
        try:
            if not self.page: raise Exception("Browser not initialized")
            await self.page.fill(selector, text)
            return {"success": True, "message": f"Filled {selector}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def take_screenshot(self, path: str = "screenshot.png", full_page: bool = False) -> Dict[str, Any]:
        """Take a screenshot of the current page."""
        try:
            if not self.page:
                return {"success": False, "error": "No page loaded"}
            
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            await self.page.screenshot(path=path, full_page=full_page)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def search(self, query: str) -> Dict[str, Any]:
        """Perform a web search using Google."""
        try:
            await self.initialize()
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            nav_result = await self.navigate(search_url)
            if not nav_result["success"]:
                return nav_result
            
            return await self.extract_content()
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close(self):
        """Close the browser and cleanup."""
        try:
            if self.page: await self.page.close()
            if self.context: await self.context.close()
            if self.browser: await self.browser.close()
            if self._playwright: await self._playwright.stop()
            logger.info("Browser closed and cleaned up")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")
        finally:
            self.browser = None
            self.context = None
            self.page = None
            self._playwright = None

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
