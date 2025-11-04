"""
Utilities for mapping streaming tracks to YouTube sources.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from ..youtube_search import SearchResult, YouTubeSearcher
from .models import ResolutionCandidate, StreamingTrack

logger = logging.getLogger(__name__)


class TrackResolver:
    """Generates ranked YouTube candidates for a given streaming track."""

    def __init__(self, searcher: Optional[YouTubeSearcher] = None):
        self._searcher = searcher or YouTubeSearcher()

    def generate_candidates(
        self,
        track: StreamingTrack,
        limit: int = 5,
    ) -> List[ResolutionCandidate]:
        """
        Return ranked candidates derived from YouTube search results.
        """
        query = track.canonical_query()
        logger.info("Resolving track via YouTube search: %s", query)
        results = self._searcher.search_videos(query, limit=max(limit * 2, 10))

        candidates: List[ResolutionCandidate] = []
        for result in results:
            score = self._score_candidate(track, result)
            candidate = ResolutionCandidate(
                youtube_id=result.video_id,
                url=result.url,
                title=result.title,
                channel=result.channel,
                duration_sec=result.duration_sec,
                view_count=result.view_count,
                score=score,
            )
            candidates.append(candidate)

        candidates.sort(key=lambda item: item.score, reverse=True)
        if len(candidates) > limit:
            return candidates[:limit]
        return candidates

    def pick_best(self, track: StreamingTrack) -> Optional[ResolutionCandidate]:
        """
        Convenience helper that returns the highest scoring candidate, if any.
        """
        candidates = self.generate_candidates(track, limit=1)
        return candidates[0] if candidates else None

    def _score_candidate(self, track: StreamingTrack, result: SearchResult) -> float:
        """
        Compute a heuristic score combining duration similarity and metadata overlap.
        """
        score = 0.0

        # Base score from YouTube ranking
        score += result.ranking_score

        # Duration similarity (penalize >5% difference)
        if track.duration_ms and result.duration_sec:
            expected = track.duration_ms / 1000
            diff = abs(expected - result.duration_sec)
            tolerance = max(5.0, expected * 0.05)
            if diff <= tolerance:
                score += 40
            else:
                score -= min(30, diff)

        # Artist/title keyword checks
        title_lower = result.title.lower()
        artist_tokens = [name.lower() for name in track.artists]
        if any(token in title_lower for token in artist_tokens):
            score += 15
        if track.name.lower() in title_lower:
            score += 15

        # Penalty for lyric/live indicators
        lowered = result.title.lower()
        if "lyric" in lowered and "official" not in lowered:
            score -= 10
        if "live" in lowered:
            score -= 20

        return score
