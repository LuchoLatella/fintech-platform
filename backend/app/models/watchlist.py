"""
Re-exporta Watchlist y WatchlistItem desde app.models.asset
para mantener imports limpios en los routers.
"""
from app.models.asset import Watchlist, WatchlistItem

__all__ = ["Watchlist", "WatchlistItem"]