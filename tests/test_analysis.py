import analysis


def _video(title="My Song", duration="PT3M30S", views=5000, likes=200, comments=20, description=""):
    return {
        "snippet": {"title": title, "description": description, "channelTitle": "Some Artist"},
        "statistics": {"viewCount": str(views), "likeCount": str(likes), "commentCount": str(comments)},
        "contentDetails": {"duration": duration},
    }


def _channel(subs=2000, country="IS"):
    snippet = {"title": "Some Artist"}
    if country:
        snippet["country"] = country
    return {"snippet": snippet, "statistics": {"subscriberCount": str(subs)}}


def _search_item(video_id="v1", channel_id="c1"):
    return {"id": {"videoId": video_id}, "snippet": {"channelId": channel_id}}


def test_parse_duration_handles_bad_input():
    assert analysis.parse_duration("PT1M") == 60
    assert analysis.parse_duration(None) == 0
    assert analysis.parse_duration("garbage") == 0


def test_duration_bounds():
    assert analysis.is_valid_music_track(_video()["snippet"], _video())
    short = _video(duration="PT1M")
    assert not analysis.is_valid_music_track(short["snippet"], short)
    long_ = _video(duration="PT15M")
    assert not analysis.is_valid_music_track(long_["snippet"], long_)


def test_negative_keywords_in_title_or_description():
    v = _video(title="Song (Lyric Video)")
    assert not analysis.is_valid_music_track(v["snippet"], v)
    v = _video(description="a cover of a classic")
    assert not analysis.is_valid_music_track(v["snippet"], v)


def test_traction_score_rejects_out_of_range():
    v = _video(views=10)
    assert analysis.calculate_traction_score(v["snippet"], v["statistics"], {"subscriberCount": "2000"}) == 0
    v = _video(views=5000)
    assert analysis.calculate_traction_score(v["snippet"], v["statistics"], {"subscriberCount": "10"}) == 0
    assert analysis.calculate_traction_score(v["snippet"], v["statistics"], {"subscriberCount": "5000000"}) == 0


def test_traction_score_missing_stats_does_not_crash():
    assert analysis.calculate_traction_score({}, {}, {}) == 0


def test_process_and_score_videos_end_to_end():
    results = analysis.process_and_score_videos(
        [_search_item()], {"v1": _video()}, {"c1": _channel()}
    )
    assert len(results) == 1
    track = results[0]
    assert track["video_id"] == "v1"
    assert track["country"] == "IS"
    assert track["final_score"] > 0


def test_smaller_country_scores_higher():
    small = analysis.process_and_score_videos([_search_item()], {"v1": _video()}, {"c1": _channel(country="IS")})
    big = analysis.process_and_score_videos([_search_item()], {"v1": _video()}, {"c1": _channel(country="US")})
    assert small[0]["final_score"] > big[0]["final_score"]


def test_missing_details_are_skipped():
    assert analysis.process_and_score_videos([_search_item()], {}, {"c1": _channel()}) == []
    unknown_country = analysis.process_and_score_videos([_search_item()], {"v1": _video()}, {"c1": _channel(country=None)})
    assert unknown_country[0]["country"] == "unknown"
