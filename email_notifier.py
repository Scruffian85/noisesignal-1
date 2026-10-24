"""
Email notification module for NoiseSignal automation.
Sends weekly summaries and error alerts via Gmail SMTP.
"""

import html
import smtplib
import ssl
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Optional

class EmailNotifier:
    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = os.getenv("GMAIL_ADDRESS")
        self.sender_password = os.getenv("GMAIL_APP_PASSWORD")
        self.recipient_email = os.getenv("NOTIFICATION_EMAIL", "daddyfandango@gmail.com")

        if not self.sender_email or not self.sender_password:
            logging.warning("Gmail credentials not found in environment variables")

    def send_email(self, subject: str, html_content: str, text_content: str = None) -> bool:
        """Send an email with both HTML and plain text content."""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = self.recipient_email

            # Create plain text version if not provided
            if text_content is None:
                text_content = self._html_to_text(html_content)

            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")

            message.attach(text_part)
            message.attach(html_part)

            # Create secure connection and send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipient_email, message.as_string())

            logging.info(f"Email sent successfully to {self.recipient_email}")
            return True

        except Exception as e:
            logging.error(f"Failed to send email: {e}")
            return False

    def send_weekly_summary(self, tracks: List[Dict], playlist_url: str, execution_time: str) -> bool:
        """Send weekly summary of discovered tracks."""
        subject = f"🎵 NoiseSignal Weekly Discovery - {len(tracks)} New Tracks"

        html_content = self._generate_weekly_summary_html(tracks, playlist_url, execution_time)
        text_content = self._generate_weekly_summary_text(tracks, playlist_url, execution_time)

        return self.send_email(subject, html_content, text_content)

    def send_error_alert(self, error_type: str, error_message: str, execution_time: str) -> bool:
        """Send error alert for failed executions."""
        subject = f"⚠️ NoiseSignal Error Alert - {error_type}"

        html_content = self._generate_error_alert_html(error_type, error_message, execution_time)
        text_content = self._generate_error_alert_text(error_type, error_message, execution_time)

        return self.send_email(subject, html_content, text_content)

    def send_success_notification(self, tracks_added: int, playlist_url: str, execution_time: str) -> bool:
        """Send simple success notification."""
        subject = f"✅ NoiseSignal Complete - {tracks_added} tracks added"

        html_content = f"""
        <html>
        <body>
            <h2>🎵 NoiseSignal Execution Complete</h2>
            <p><strong>Execution Time:</strong> {execution_time}</p>
            <p><strong>Tracks Added:</strong> {tracks_added}</p>
            <p><strong>Playlist:</strong> <a href="{playlist_url}">Global Emerging Tracks</a></p>
            <p>Ready for your weekly music discovery session!</p>
        </body>
        </html>
        """

        text_content = f"""
        NoiseSignal Execution Complete

        Execution Time: {execution_time}
        Tracks Added: {tracks_added}
        Playlist: {playlist_url}

        Ready for your weekly music discovery session!
        """

        return self.send_email(subject, html_content, text_content)

    def _generate_weekly_summary_html(self, tracks: List[Dict], playlist_url: str, execution_time: str) -> str:
        """Generate HTML content for weekly summary email."""
        playlist_url = html.escape(str(playlist_url), quote=True)
        tracks_html = ""
        for i, track in enumerate(tracks[:10], 1):  # Show top 10
            tracks_html += f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 8px;">{i}</td>
                <td style="padding: 8px;"><strong>{html.escape(str(track.get('title', 'Unknown')))}</strong></td>
                <td style="padding: 8px;">{html.escape(str(track.get('artist', 'Unknown')))}</td>
                <td style="padding: 8px;">{html.escape(str(track.get('country', 'Unknown')))}</td>
                <td style="padding: 8px;">{track.get('views', 0):,}</td>
                <td style="padding: 8px;">{track.get('final_score', 0):.2f}</td>
            </tr>
            """

        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #1a73e8; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th {{ background-color: #f5f5f5; padding: 10px; text-align: left; }}
                .playlist-link {{ background-color: #1a73e8; color: white; padding: 10px 20px;
                                text-decoration: none; border-radius: 5px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎵 NoiseSignal Weekly Discovery</h1>
                <p>Your automated music discovery results</p>
            </div>

            <div class="content">
                <p><strong>Execution Time:</strong> {execution_time}</p>
                <p><strong>Total Tracks Discovered:</strong> {len(tracks)}</p>

                <p style="margin: 20px 0;">
                    <a href="{playlist_url}" class="playlist-link">🎧 Listen to Playlist</a>
                </p>

                <h2>Top 10 Discoveries</h2>
                <table border="1">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Track</th>
                            <th>Artist</th>
                            <th>Country</th>
                            <th>Views</th>
                            <th>Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        {tracks_html}
                    </tbody>
                </table>

                <p style="color: #666; font-size: 0.9em; margin-top: 30px;">
                    Generated by NoiseSignal automation system<br>
                    Happy music discovery! 🎶
                </p>
            </div>
        </body>
        </html>
        """

    def _generate_weekly_summary_text(self, tracks: List[Dict], playlist_url: str, execution_time: str) -> str:
        """Generate plain text content for weekly summary email."""
        tracks_text = ""
        for i, track in enumerate(tracks[:10], 1):
            tracks_text += f"{i}. {track.get('title', 'Unknown')} - {track.get('artist', 'Unknown')} ({track.get('country', 'Unknown')}) - {track.get('views', 0):,} views\n"

        return f"""
NoiseSignal Weekly Discovery

Execution Time: {execution_time}
Total Tracks Discovered: {len(tracks)}

Playlist: {playlist_url}

Top 10 Discoveries:
{tracks_text}

Generated by NoiseSignal automation system
Happy music discovery!
        """

    def _generate_error_alert_html(self, error_type: str, error_message: str, execution_time: str) -> str:
        """Generate HTML content for error alert email."""
        error_type = html.escape(str(error_type))
        error_message = html.escape(str(error_message))
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .error-box {{ background-color: #f8d7da; border: 1px solid #f5c6cb;
                             border-radius: 5px; padding: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⚠️ NoiseSignal Error Alert</h1>
                <p>Automated execution encountered an issue</p>
            </div>

            <div class="content">
                <p><strong>Execution Time:</strong> {execution_time}</p>
                <p><strong>Error Type:</strong> {error_type}</p>

                <div class="error-box">
                    <h3>Error Details:</h3>
                    <pre>{error_message}</pre>
                </div>

                <h3>Recommended Actions:</h3>
                <ul>
                    <li>Check the application logs for more details</li>
                    <li>Verify YouTube API credentials and quotas</li>
                    <li>Ensure internet connectivity is stable</li>
                    <li>Consider running manually to diagnose the issue</li>
                </ul>

                <p style="color: #666; font-size: 0.9em; margin-top: 30px;">
                    Generated by NoiseSignal automation system
                </p>
            </div>
        </body>
        </html>
        """

    def _generate_error_alert_text(self, error_type: str, error_message: str, execution_time: str) -> str:
        """Generate plain text content for error alert email."""
        return f"""
NoiseSignal Error Alert

Execution Time: {execution_time}
Error Type: {error_type}

Error Details:
{error_message}

Recommended Actions:
- Check the application logs for more details
- Verify YouTube API credentials and quotas
- Ensure internet connectivity is stable
- Consider running manually to diagnose the issue

Generated by NoiseSignal automation system
        """

    def _html_to_text(self, html_content: str) -> str:
        """Simple HTML to text conversion for plain text email fallback."""
        import re

        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html_content)

        # Replace HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')

        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()

        return text