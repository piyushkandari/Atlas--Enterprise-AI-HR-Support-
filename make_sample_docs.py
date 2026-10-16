"""Create sample policy PDFs and IT knowledge-base text files.

Run once from the project root:
    python make_sample_docs.py

Creates:
    data/policies/leave_policy.pdf
    data/policies/payroll_policy.pdf
    data/policies/code_of_conduct.pdf
    data/it_kb/vpn_setup.txt
    data/it_kb/printer_issues.txt
    data/it_kb/password_reset.txt
    data/it_kb/wifi_troubleshooting.txt
"""
from pathlib import Path

from fpdf import FPDF


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

POLICIES = {
    "leave_policy.pdf": """
Company Leave Policy
====================

1. Leave types
   - Casual Leave: 12 days per calendar year.
   - Sick Leave: 8 days per calendar year.
   - Earned Leave: 15 days per calendar year, accrues monthly.

2. Applying for leave
   - All leave must be applied through the HR portal at least 3 working days in advance.
   - Manager approval is required for any leave longer than 2 days.
   - Sick leave longer than 3 days requires a medical certificate.

3. Weekends and holidays
   - Saturdays and Sundays are not counted as leave days.
   - Public holidays declared by the company are not counted as leave days.

4. Carry forward
   - Up to 5 unused Earned Leave days carry forward to the next year.
   - Casual and Sick Leave do not carry forward.

5. Leave without pay
   - If the balance is exhausted, employees may take unpaid leave with HR approval.
""",

    "payroll_policy.pdf": """
Payroll Policy
==============

1. Salary cycle
   - Salaries are paid on the last working day of every month.
   - Payslips are available in the HR portal from the 1st of the following month.

2. Components
   - Basic salary is 50% of CTC.
   - HRA is 40% of basic salary.
   - Special allowance makes up the rest.
   - Deductions include PF (12% of basic), professional tax and TDS.

3. Provident Fund (PF)
   - Employee contribution: 12% of basic salary.
   - Employer contribution: 12% of basic salary.
   - PF balance can be checked in the HR portal any time.

4. Income tax
   - TDS is deducted as per the employee's declared tax regime.
   - Declarations must be submitted by 31 January every year.

5. Bonus
   - Annual bonus is paid with the December salary.
   - Eligibility: 6 months of continuous service in the calendar year.
""",

    "code_of_conduct.pdf": """
Code of Conduct
===============

1. Professional behaviour
   - Treat colleagues, clients and partners with respect.
   - Harassment and discrimination are strictly prohibited.

2. Confidentiality
   - Company data, customer data and internal documents are confidential.
   - Sharing outside the company requires written approval from your manager.

3. Use of company assets
   - Laptops, phones and network access are for business use.
   - Limited personal use is acceptable if it does not affect work.

4. Conflict of interest
   - Disclose any outside employment or business to HR.
   - Do not use your position for personal gain.

5. Reporting violations
   - Report violations to your manager or to ethics@company.com.
   - Retaliation against reporters is prohibited.

6. Disciplinary action
   - Violations may result in warnings, suspension or termination.
""",
}


IT_KB = {
    "vpn_setup.txt": """VPN Setup Guide

Applies to: All employees using company laptops (Windows / macOS / Linux)

Steps:
1. Open the company portal at https://portal.company.com.
2. Download the GlobalConnect VPN client for your OS.
3. Install it and launch. The server address is vpn.company.com.
4. Sign in with your company email and SSO password.
5. Approve the MFA push notification on your phone.
6. Confirm status says "Connected - Bangalore-1".

Troubleshooting:
- If MFA push doesn't arrive, check that the Authenticator app is installed.
- If you see "Server unreachable", try a different network (mobile hotspot).
- If it still fails, raise an IT ticket with category=Network.
""",

    "printer_issues.txt": """Printer Troubleshooting

Common problems:
1. Printer not visible on the network.
   - Confirm you're on office Wi-Fi, not VPN.
   - Restart the print spooler:
     Windows: services.msc -> Print Spooler -> Restart.
2. Print jobs stuck in queue.
   - Open Printers & Scanners -> open the queue -> cancel all -> retry.
3. "Access denied" when printing to a shared printer.
   - You need to be a member of the "Office-Printers" AD group.
   - Raise a ticket with category=Hardware and mention the printer name.

Escalation:
If none of the above works, raise an IT ticket. Attach a photo
of the printer's error LED if the printer has one.
""",

    "password_reset.txt": """Password Reset

Self-service reset:
1. Go to https://sso.company.com/reset.
2. Enter your company email.
3. Verify via OTP sent to your registered phone.
4. Set a new password:
   - Minimum 12 characters.
   - Must include upper, lower, digit and a symbol.
   - Cannot reuse the last 5 passwords.

If your account is locked (5 wrong attempts):
- Wait 30 minutes and retry, or raise a ticket with category=Access.
- Include your employee code in the ticket.

Password expiry: every 90 days. You'll get an email 7 days before.
""",

    "wifi_troubleshooting.txt": """Wi-Fi Troubleshooting

Network: COMP-CORP (employees), COMP-GUEST (visitors)

Common issues:
1. Can't see COMP-CORP.
   - Forget the network and rejoin. Enter SSO credentials.
2. Connected but no internet.
   - Open a browser; the captive portal may need you to accept terms.
3. Slow speed.
   - Switch to the 5 GHz SSID: COMP-CORP-5G.
4. Certificate error on first connect.
   - Accept the certificate; it's the internal CA.

If problems persist, raise a ticket with category=Network.
""",
}


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_pdfs(out_dir: Path) -> list[Path]:
    """Write one PDF per entry in POLICIES. Returns the list of files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []

    for filename, text in POLICIES.items():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)

        for line in text.strip().splitlines():
            # fpdf2's core font can't render non-latin chars; sanitize.
            safe = line.encode("latin-1", "replace").decode("latin-1")
            # Pass effective page width (pdf.epw) so multi_cell always has room.
            pdf.multi_cell(pdf.epw, 6, safe)

        path = out_dir / filename
        pdf.output(str(path))
        written.append(path)

    return written


def write_texts(out_dir: Path) -> list[Path]:
    """Write one .txt file per entry in IT_KB. Returns the list of files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []

    for filename, text in IT_KB.items():
        path = out_dir / filename
        path.write_text(text, encoding="utf-8")
        written.append(path)

    return written


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    policy_dir = Path("data/policies")
    it_kb_dir = Path("data/it_kb")

    print("Writing policy PDFs...")
    for path in write_pdfs(policy_dir):
        size = path.stat().st_size
        print(f"  {path}  ({size} bytes)")

    print("Writing IT KB articles...")
    for path in write_texts(it_kb_dir):
        size = path.stat().st_size
        print(f"  {path}  ({size} bytes)")

    print()
    print("Done.")
    print(f"  policies : {policy_dir}/")
    print(f"  IT KB    : {it_kb_dir}/")
    print()
    print("Next step:  python -m rag.ingest")


if __name__ == "__main__":
    main()