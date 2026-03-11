import os
import argparse
import sys
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

class GoogleBotAuditor:
    def __init__(self, creds_path):
        self.scopes = ['https://www.googleapis.com/auth/chat.bot']
        
        if not os.path.exists(creds_path):
            print(f"[!] Error: Credentials file not found at {creds_path}")
            sys.exit(1)
            
        self.creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=self.scopes)
        self.service = build('chat', 'v1', credentials=self.creds)

    def perform_recon(self, space_id):
        """Retrieves metadata and member list for a specific space."""
        print(f"\n[*] RECONNAISSANCE: {space_id}")
        try:
            space_info = self.service.spaces().get(name=space_id).execute()
            s_type = space_info.get('spaceType', 'UNKNOWN')
            s_display = space_info.get('displayName', 'Direct Message (1:1)')
            
            print(f"    [>] Name: {s_display}")
            print(f"    [>] Type: {s_type}")

            members_res = self.service.spaces().members().list(parent=space_id).execute()
            members = members_res.get('memberships', [])
            
            print(f"    [>] Members ({len(members)}):")
            for m in members:
                user = m.get('member', {})
                print(f"        - {user.get('displayName', 'Unknown')} [{user.get('type')}]")
            return s_display
        except Exception as e:
            print(f"    [-] RECON FAILED: {e}")
            return None

    def construct_system_alert_card(self, space_id, space_name, alert_text):
        """Builds a formal 'System Alert' CardV2 JSON structure."""
        # Note: In a real audit, the 'iconUrl' should point to a real icon (e.g., a shield).
        icon_url = "https://developers.google.com/chat/images/chat-product-icon.png"
        
        # The CardV2 structure
        card = {
            "cardsV2": [{
                "cardId": "system_alert_01",
                "card": {
                    "header": {
                        "title": "SYSTEM SECURITY ALERT",
                        "subtitle": f"See below for details",
                        "imageUrl": icon_url,
                        "imageType": "CIRCLE"
                    },
                    "sections": [{
                        "header": "Audit Findings",
                        "collapsible": False,
                        "uncollapsibleWidgetsCount": 1,
                        "widgets": [
                            {
                                "textParagraph": {
                                    "text": f"<b>Warning:</b> Unverified application presence detected in this space. Proceed with caution when sharing credentials and raise security on-call ticket if compromised.<br><br>{alert_text}"
                                }
                            },
                            {
                                "decoratedText": {
                                    "topLabel": "Space ID",
                                    "text": space_id,
                                    "bottomLabel": "Verify with Admin Console",
                                    "wrapText": True
                                }
                            }
                        ]
                    }]
                }
            }]
        }
        return card

    def send_message(self, space_id, text=None, card_payload=None):
        """
        Versatile delivery logic: Sends card if provided, else plaintext.
        """
        payload = {}
        if card_payload:
            # We are sending an interactive card
            payload = card_payload
            msg_type = "CARD"
        elif text:
            # Reverting to basic plaintext
            payload = {'text': text}
            msg_type = "PLAINTEXT"
        else:
            print(f"[-] Error: Nothing to send to {space_id}")
            return

        try:
            self.service.spaces().messages().create(
                parent=space_id, 
                body=payload
            ).execute()
            print(f"    [+] {msg_type} DELIVERY SUCCESS: {space_id}")
        except Exception as e:
            print(f"    [-] DELIVERY FAILED to {space_id}: {e}")

    def run(self, msg_text=None, target_space=None, use_card=False):
        print("\n" + "="*60)
        print("[!] GOOGLE BOT AUDIT & MESSAGING TOOL (MULTI-MODE)")
        print("="*60)
        
        try:
            # Step 1: Discovery
            spaces_res = self.service.spaces().list().execute()
            all_spaces = spaces_res.get('spaces', [])
            
            if not all_spaces:
                print("[-] No accessible spaces found. Is the bot added to any rooms?")
                return

            targets = []
            if target_space:
                # Add a single tuple: (id, "Targeted Mode")
                targets.append((target_space, "Targeted Mode"))
            else:
                for s in all_spaces:
                    targets.append((s['name'], s.get('displayName', 'DM')))

            # Step 2: Process Targets
            print(f"[+] Operational Plan: Messaging {len(targets)} space(s).")
            for t_id, t_name in targets:
                # Always run recon first for audit context
                current_space_name = self.perform_recon(t_id)
                
                # Step 3: Deliver based on mode (Targeted or Blast)
                if not msg_text and not use_card:
                    continue # Recon only mode
                
                final_payload = None
                if use_card:
                    # Construct and send the advanced System Alert card
                    card_text = msg_text if msg_text else "Audit completed. Check findings."
                    final_payload = self.construct_system_alert_card(t_id, current_space_name, card_text)
                    self.send_message(t_id, card_payload=final_payload)
                else:
                    # Default back to basic plaintext
                    self.send_message(t_id, text=msg_text)

            print("\n" + "="*60)
            print("[+] OPERATION COMPLETE")

        except Exception as e:
            print(f"[!] Critical Error: {e}")

# --- CLI WRAPPER ---

def main():
    parser = argparse.ArgumentParser(description="Google Chat Bot Auditor: Recon, Target, and Multi-Format Messaging")
    parser.add_argument("-c", "--creds", required=True, help="Path to service_account.json")
    parser.add_argument("-b", "--blast", help="The message text (plaintext or card body)")
    parser.add_argument("-t", "--target", help="Specific Space ID to message")
    parser.add_argument("--card", action="store_true", help="Send the message as a 'System Alert' Card")
    
    args = parser.parse_args()

    # Require a message if using blast or target flags
    if (args.blast or args.target) and not args.blast:
        print("[!] Error: --blast text is required when using --target or making a delivery.")
        sys.exit(1)

    auditor = GoogleBotAuditor(args.creds)
    auditor.run(msg_text=args.blast, target_space=args.target, use_card=args.card)

if __name__ == "__main__":
    main()
