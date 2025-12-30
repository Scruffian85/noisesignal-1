#!/usr/bin/env python3
"""
Test script for email notifications without requiring Gmail credentials.
This validates the email generation logic.
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from email_notifier import EmailNotifier

def test_email_generation():
    """Test email content generation without actually sending emails."""
    print("🧪 Testing NoiseSignal Email Notification System")
    print("=" * 50)

    # Create test data
    test_tracks = [
        {
            'title': 'Midnight Echoes',
            'artist': 'Luna Dreams',
            'country': 'IS',
            'views': 1250,
            'likes': 89,
            'comments': 15,
            'subscribers': 2100,
            'final_score': 8.5,
            'video_id': 'test123'
        },
        {
            'title': 'Digital Sunrise',
            'artist': 'Neon Collective',
            'country': 'NO',
            'views': 3400,
            'likes': 156,
            'comments': 32,
            'subscribers': 4500,
            'final_score': 7.8,
            'video_id': 'test456'
        }
    ]

    playlist_url = "https://www.youtube.com/playlist?list=PLtest123"
    execution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Test email notifier creation
    try:
        notifier = EmailNotifier()
        print("✓ EmailNotifier created successfully")
    except Exception as e:
        print(f"✗ Failed to create EmailNotifier: {e}")
        return False

    # Test weekly summary generation
    try:
        html_content = notifier._generate_weekly_summary_html(test_tracks, playlist_url, execution_time)
        text_content = notifier._generate_weekly_summary_text(test_tracks, playlist_url, execution_time)

        print("✓ Weekly summary email content generated")
        print(f"  HTML length: {len(html_content)} characters")
        print(f"  Text length: {len(text_content)} characters")

        # Save sample HTML for inspection
        with open("sample_weekly_email.html", "w") as f:
            f.write(html_content)
        print("✓ Sample HTML saved to 'sample_weekly_email.html'")

    except Exception as e:
        print(f"✗ Failed to generate weekly summary: {e}")
        return False

    # Test error alert generation
    try:
        error_html = notifier._generate_error_alert_html(
            "Authentication Failed",
            "YouTube API authentication failed. Please check credentials.",
            execution_time
        )
        error_text = notifier._generate_error_alert_text(
            "Authentication Failed",
            "YouTube API authentication failed. Please check credentials.",
            execution_time
        )

        print("✓ Error alert email content generated")
        print(f"  HTML length: {len(error_html)} characters")
        print(f"  Text length: {len(error_text)} characters")

        # Save sample HTML for inspection
        with open("sample_error_email.html", "w") as f:
            f.write(error_html)
        print("✓ Sample error HTML saved to 'sample_error_email.html'")

    except Exception as e:
        print(f"✗ Failed to generate error alert: {e}")
        return False

    # Test HTML to text conversion
    try:
        test_html = "<h1>Test</h1><p>This is a <strong>test</strong> email.</p>"
        converted_text = notifier._html_to_text(test_html)

        print("✓ HTML to text conversion works")
        print(f"  Original: {test_html}")
        print(f"  Converted: {converted_text}")

    except Exception as e:
        print(f"✗ Failed HTML to text conversion: {e}")
        return False

    print("\n" + "=" * 50)
    print("🎉 All email notification tests passed!")
    print("\nNext steps for deployment:")
    print("1. Set up Gmail app password in .env file")
    print("2. Test with actual email sending")
    print("3. Deploy with Docker")

    return True

if __name__ == "__main__":
    success = test_email_generation()
    sys.exit(0 if success else 1)