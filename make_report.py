#!/usr/bin/env python3
"""Builds YourName_EWB_VPC_Peering.pdf from ids.env, evidence/*.txt and screenshots/*.png|jpg.
Run:  python3 make_report.py     (pip install reportlab pillow  if missing)
Edit my_notes.txt to personalise the 'What I learned' section."""
import glob, os, re, textwrap, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak,
                                Preformatted, Table, TableStyle, KeepTogether, Image, NextPageTemplate)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
def rd(p):
    try: return open(os.path.join(HERE, p), encoding="utf-8", errors="replace").read()
    except FileNotFoundError: return None
def load_env(path):
    d = {}
    for line in (rd(path) or "").splitlines():
        m = re.match(r'^([A-Z_0-9]+)="?(.*?)"?$', line.strip())
        if m: d[m.group(1)] = m.group(2)
    return d
cfg = load_env("config.env")
ids_file = "ids.env"
if not (rd(ids_file) or "").strip():
    cands = sorted(glob.glob(os.path.join(HERE, "ids.env.cleaned-*")))
    if cands: ids_file = os.path.basename(cands[-1])
ids = load_env(ids_file)
STUDENT = cfg.get("STUDENT", "Your Name"); BATCH = cfg.get("BATCH", "Your Batch"); REGION = cfg.get("REGION", "ap-south-1")
safe = re.sub(r"[^A-Za-z0-9]+", "", STUDENT) or "YourName"
OUT = os.path.join(HERE, f"{safe}_EWB_VPC_Peering.pdf")

NAVY = colors.HexColor("#0A1230"); BLUE = colors.HexColor("#00A3FF"); LIME = colors.HexColor("#A6FF00")
CREAM = colors.HexColor("#F4F0E8"); GREY = colors.HexColor("#5B6475"); LIGHT = colors.HexColor("#EAF6FD")
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=18, textColor=NAVY, spaceBefore=4, spaceAfter=6)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=12, textColor=NAVY, spaceBefore=10, spaceAfter=4)
B  = ParagraphStyle("B", parent=ss["BodyText"], fontName="Helvetica", fontSize=10, leading=14.5, textColor=colors.HexColor("#1B2133"))
SM = ParagraphStyle("SM", parent=B, fontSize=8.5, leading=11, textColor=GREY)
CAP = ParagraphStyle("CAP", parent=B, fontSize=8.5, leading=11, textColor=NAVY, fontName="Helvetica-Bold", spaceBefore=3, spaceAfter=2)
MONO = ParagraphStyle("MONO", fontName="Courier", fontSize=7.2, leading=9, textColor=colors.HexColor("#E6EDF7"))
CELL = ParagraphStyle("CELL", parent=B, fontSize=8.5, leading=11)
CELLB = ParagraphStyle("CELLB", parent=CELL, fontName="Helvetica-Bold", textColor=colors.white)

def P(t, s=B): return Paragraph(t, s)
def esc(t): return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
def code(path, title, expect=None):
    raw = rd(path); out = [P(title, CAP)]
    if raw is None:
        out.append(P(f"<font color='#C62828'>[Evidence file {path} not captured yet - run the matching script]</font>", SM)); return out
    lines = []
    for ln in raw.rstrip().splitlines(): lines += textwrap.wrap(ln, 112, subsequent_indent="    ", replace_whitespace=False) or [""]
    t = Table([[Preformatted("\n".join(lines), MONO)]], colWidths=[174*mm])
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), NAVY), ("LEFTPADDING", (0,0), (-1,-1), 7), ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
    out.append(t)
    if expect: out.append(P(f"<b>Result:</b> {expect}", SM))
    return out
def table(rows, widths, header=True):
    data = [[Paragraph(esc(str(c)), CELLB if (header and i == 0) else CELL) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#D5DAE3")), ("VALIGN", (0,0), (-1,-1), "TOP"),
          ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F3F7FA")])]
    if header: st.append(("BACKGROUND", (0,0), (-1,0), NAVY))
    t.setStyle(TableStyle(st)); return t
def callout(text, bg=LIGHT, bar=BLUE):
    t = Table([[Paragraph(text, B)]], colWidths=[174*mm])
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), bg), ("LINEBEFORE", (0,0), (0,-1), 3, bar), ("LEFTPADDING", (0,0), (-1,-1), 9), ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
    return t

def diagram():
    d = Drawing(174*mm, 98*mm); W = 174*mm
    def box(x, y, w, h, fill, stroke, title=None, lines=(), tc=NAVY):
        d.add(Rect(x, y, w, h, rx=5, ry=5, fillColor=fill, strokeColor=stroke, strokeWidth=1.2))
        if title: d.add(String(x+6, y+h-13, title, fontName="Helvetica-Bold", fontSize=9, fillColor=tc))
        for i, l in enumerate(lines): d.add(String(x+6, y+h-25-i*10, l, fontName="Helvetica", fontSize=7.5, fillColor=GREY))
    def arrow(x1, y1, x2, y2, c=BLUE, w=1.6):
        d.add(Line(x1, y1, x2, y2, strokeColor=c, strokeWidth=w))
    box(5*mm, 80*mm, 50*mm, 14*mm, CREAM, GREY, "Your laptop", ["SSH key + ~/.ssh/config"])
    box(75*mm, 80*mm, 50*mm, 14*mm, CREAM, GREY, "Internet gateway", ["ewb-igw-a (attached to VPC A)"])
    arrow(55*mm, 87*mm, 75*mm, 87*mm); d.add(String(57*mm, 89*mm, "SSH/22", fontName="Helvetica", fontSize=6.5, fillColor=GREY))
    box(5*mm, 3*mm, 82*mm, 73*mm, LIGHT, colors.HexColor("#8CC8E8"), "VPC A  ewb-vpc-a  10.10.0.0/16")
    box(9*mm, 40*mm, 74*mm, 28*mm, colors.white, colors.HexColor("#B9D7E6"), "Public subnet  ewb-a-public", ["10.10.1.0/24", "ewb-bastion  10.10.1.10 + public IPv4", "Route: 0.0.0.0/0 -> IGW ; 10.20.0.0/16 -> pcx"])
    box(9*mm, 7*mm, 74*mm, 28*mm, colors.white, colors.HexColor("#B9D7E6"), "Private subnet  ewb-a-private", ["10.10.2.0/24", "ewb-app-a  10.10.2.10  (no public IP)", "Route: 10.20.0.0/16 -> pcx"])
    box(92*mm, 3*mm, 77*mm, 73*mm, colors.HexColor("#F3F8EC"), colors.HexColor("#A7C77A"), "VPC B  ewb-vpc-b  10.20.0.0/16", ["No internet gateway"])
    box(96*mm, 7*mm, 69*mm, 28*mm, colors.white, colors.HexColor("#C5DBA0"), "Private subnet  ewb-b-private", ["10.20.1.0/24", "ewb-app-b  10.20.1.10  (no public IP)", "Route: 10.10.0.0/16 -> pcx"])
    arrow(125*mm, 87*mm, 125*mm, 87*mm)
    arrow(46*mm, 80*mm, 46*mm, 68*mm)                               # IGW/laptop into public subnet (conceptual)
    arrow(83*mm, 54*mm, 130*mm, 54*mm, c=NAVY, w=1.1); arrow(130*mm, 54*mm, 130*mm, 35*mm, c=NAVY, w=1.1)
    d.add(String(96*mm, 56*mm, "SSH via bastion (ProxyJump)", fontName="Helvetica", fontSize=7, fillColor=NAVY))
    arrow(46*mm, 40*mm, 46*mm, 35*mm, c=NAVY, w=1.1)
    d.add(Rect(83*mm, 18*mm, 13*mm, 8*mm, fillColor=NAVY, strokeColor=NAVY))
    d.add(String(84.5*mm, 21*mm, "PEERING", fontName="Helvetica-Bold", fontSize=5.5, fillColor=colors.white))
    arrow(83*mm, 22*mm, 83*mm, 22*mm); arrow(78*mm, 22*mm, 83*mm, 22*mm, c=LIME, w=2.5); arrow(96*mm, 22*mm, 99*mm, 22*mm, c=LIME, w=2.5)
    return d

def decorate(canvas, doc):
    canvas.saveState(); w, h = A4
    canvas.setFillColor(CREAM); canvas.rect(0, h-18*mm, w, 18*mm, stroke=0, fill=1)
    canvas.setFillColor(NAVY); canvas.setFont("Helvetica-Bold", 10); canvas.drawString(18*mm, h-11*mm, "EWB COURSES")
    canvas.setFont("Helvetica", 8); canvas.setFillColor(GREY); canvas.drawRightString(w-18*mm, h-11*mm, "AWS ARCHITECT ASSOCIATE  |  VPC PEERING PROJECT")
    canvas.setStrokeColor(colors.HexColor("#D5DAE3")); canvas.line(18*mm, 14*mm, w-18*mm, 14*mm)
    canvas.drawString(18*mm, 9*mm, f"{STUDENT}  |  {BATCH}"); canvas.drawRightString(w-18*mm, 9*mm, f"Page {doc.page}")
    canvas.restoreState()
def cover(canvas, doc):
    canvas.saveState(); w, h = A4
    canvas.setFillColor(CREAM); canvas.rect(0, 0, w, h, stroke=0, fill=1)
    canvas.setFillColor(NAVY); canvas.rect(0, 70*mm, w, 135*mm, stroke=0, fill=1)
    canvas.setFillColor(LIME); canvas.roundRect(18*mm, h-38*mm, 52*mm, 8*mm, 2, stroke=0, fill=1)
    canvas.setFillColor(NAVY); canvas.setFont("Helvetica", 8); canvas.drawString(21*mm, h-35.4*mm, "BUILD / TEST / EXPLAIN")
    canvas.setFont("Helvetica-Bold", 22); canvas.drawString(18*mm, h-22*mm, "EWB COURSES")
    canvas.setFillColor(BLUE); canvas.setFont("Helvetica", 16); canvas.drawString(18*mm, 188*mm, "AWS")
    canvas.setFillColor(colors.white); canvas.setFont("Helvetica-Bold", 40); canvas.drawString(18*mm, 170*mm, "VPC Peering")
    canvas.setFont("Helvetica", 18); canvas.drawString(18*mm, 150*mm, "Connect two VPCs. Prove private connectivity.")
    canvas.setFont("Helvetica", 10); canvas.setFillColor(colors.HexColor("#B8C2D9"))
    canvas.drawString(18*mm, 136*mm, "Project report: EC2, custom route tables, security groups and a bastion host")
    for x, lab, cidr in ((18*mm, "VPC A", "10.10.0.0/16"), (118*mm, "VPC B", "10.20.0.0/16")):
        canvas.setFillColor(colors.HexColor("#14213F")); canvas.setStrokeColor(colors.HexColor("#33466B")); canvas.roundRect(x, 90*mm, 74*mm, 32*mm, 5, stroke=1, fill=1)
        canvas.setFillColor(colors.white); canvas.setFont("Helvetica", 13); canvas.drawString(x+6*mm, 112*mm, lab)
        canvas.setFillColor(BLUE); canvas.setFont("Courier-Bold", 12); canvas.drawString(x+6*mm, 103*mm, cidr)
    canvas.setStrokeColor(LIME); canvas.setLineWidth(2.5); canvas.line(92*mm, 106*mm, 118*mm, 106*mm)
    canvas.setFillColor(LIME); canvas.setFont("Helvetica", 9); canvas.drawCentredString(105*mm, 109*mm, "pcx")
    canvas.setFillColor(colors.white); canvas.setFont("Helvetica", 7.5); canvas.drawString(18*mm, 76*mm, "2 VPCs  /  3 EC2 INSTANCES  /  1 PRIVATE CONNECTION")
    canvas.setFillColor(NAVY); canvas.setFont("Helvetica-Bold", 11); canvas.drawString(18*mm, 56*mm, "Submitted by")
    canvas.setFont("Helvetica", 11)
    for i, (k, v) in enumerate((("Name", STUDENT), ("Batch", BATCH), ("Region", f"{REGION} (Mumbai)"), ("Completed", datetime.date.today().strftime("%d %B %Y")))):
        canvas.setFillColor(GREY); canvas.drawString(18*mm, (48-i*7)*mm, k); canvas.setFillColor(NAVY); canvas.drawString(45*mm, (48-i*7)*mm, v)
    canvas.setFillColor(GREY); canvas.setFont("Helvetica", 8); canvas.drawString(18*mm, 12*mm, "LEARN.  ELEVATE.  EMPOWER.     |     PROJECT 01")
    canvas.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=24*mm, bottomMargin=20*mm,
                      title=f"{STUDENT} - AWS VPC Peering Project", author=STUDENT)
doc.addPageTemplates([PageTemplate("cover", [Frame(0, 0, 1, 1)], onPage=cover),
                      PageTemplate("body", [Frame(18*mm, 20*mm, 174*mm, A4[1]-44*mm, id="f")], onPage=decorate)])
g = lambda k: ids.get(k, "(not captured)")
S = [NextPageTemplate("body"), PageBreak()]

# 1 Overview
S += [P("1. Project overview", H1),
      P("EWB runs an application in VPC A and a second workload in VPC B. Both application servers must stay private. "
        "In this project I created VPC peering between the two VPCs so the servers exchange traffic over their private IPv4 addresses, "
        "and used one public bastion host in VPC A for administration over SSH ProxyJump. "
        "I proved the design with a failed test before peering, successful tests after peering, and a controlled failure with recovery."), Spacer(1, 6),
      callout("<b>Goals met:</b> non-overlapping CIDRs; public and private subnets with explicit route table associations; "
              "active peering with forward and return routes; least-privilege security groups (/32 sources, no 0.0.0.0/0 for SSH or ICMP); "
              "private hosts with no public IP; evidence-based testing; full cleanup."),
      P("2. Architecture", H1), diagram(),
      P("Diagram is conceptual. The bastion opens a separate SSH connection to the destination. Peering does not give VPC B internet access through VPC A.", SM), PageBreak()]

# 2 Inventory
inv = [["Resource", "Name tag", "ID", "CIDR / IP"],
       ["VPC A", "ewb-vpc-a", g("VPC_A"), "10.10.0.0/16"], ["Public subnet", "ewb-a-public", g("SUBNET_A_PUB"), "10.10.1.0/24"],
       ["Private subnet", "ewb-a-private", g("SUBNET_A_PRIV"), "10.10.2.0/24"], ["VPC B", "ewb-vpc-b", g("VPC_B"), "10.20.0.0/16"],
       ["Private subnet", "ewb-b-private", g("SUBNET_B_PRIV"), "10.20.1.0/24"], ["Internet gateway", "ewb-igw-a", g("IGW"), "attached to VPC A"],
       ["Route table", "ewb-rt-a-public", g("RT_A_PUB"), "-> ewb-a-public"], ["Route table", "ewb-rt-a-private", g("RT_A_PRIV"), "-> ewb-a-private"],
       ["Route table", "ewb-rt-b-private", g("RT_B_PRIV"), "-> ewb-b-private"], ["Security group", "ewb-sg-bastion", g("SG_BASTION"), "VPC A"],
       ["Security group", "ewb-sg-app-a", g("SG_APP_A"), "VPC A"], ["Security group", "ewb-sg-app-b", g("SG_APP_B"), "VPC B"],
       ["EC2", "ewb-bastion", g("I_BASTION"), f"10.10.1.10 + public {g('BASTION_IP')}"], ["EC2", "ewb-app-a", g("I_APP_A"), "10.10.2.10 (no public IP)"],
       ["EC2", "ewb-app-b", g("I_APP_B"), "10.20.1.10 (no public IP)"], ["Peering", "ewb-a-b-peer", g("PCX"), "VPC A <-> VPC B"], ["Key pair", "ewb-lab", "RSA .pem (kept on laptop only)", "-"]]
S += [P("3. Resource inventory (actual IDs)", H1), table(inv, [28*mm, 34*mm, 62*mm, 50*mm]), Spacer(1, 4),
      P("Every resource is tagged <b>Project = EWB-VPC-Peering</b> and <b>Student = " + esc(STUDENT) + "</b>. "
        "Why these CIDRs? 10.10.0.0/16 and 10.20.0.0/16 do not overlap, which is a hard requirement for peering. Each /24 subnet sits inside its own VPC range.", SM), PageBreak()]

# 3 Network
S += [P("4. Subnets, internet gateway and route tables", H1)]
S += code("evidence/10-inventory-vpcs-subnets.txt", "Evidence A - VPCs, subnets and internet gateway")
S += [Spacer(1, 6)] + code("evidence/11-route-tables.txt", "Evidence B - all three route tables, subnet associations and routes")
S += [Spacer(1, 6), table([["Route table", "Destination", "Target", "Why it is needed"],
      ["ewb-rt-a-public", "10.10.0.0/16", "local", "Bastion to App-A"], ["", "0.0.0.0/0", "ewb-igw-a", "Bastion internet access"], ["", "10.20.0.0/16", "pcx", "Bastion opens SSH to App-B (ProxyJump); more specific than the default route"],
      ["ewb-rt-a-private", "10.10.0.0/16", "local", "VPC A internal"], ["", "10.20.0.0/16", "pcx", "App-A to VPC B (forward path)"],
      ["ewb-rt-b-private", "10.20.0.0/16", "local", "VPC B internal"], ["", "10.10.0.0/16", "pcx", "Return path to VPC A"]], [32*mm, 28*mm, 24*mm, 90*mm]), PageBreak()]

# 4 Peering + SG
S += [P("5. Peering connection and security groups", H1)]
S += code("evidence/14-peering.txt", "Evidence C - peering ewb-a-b-peer is Active (requester VPC A, accepter VPC B)")
S += [Spacer(1, 6)] + code("evidence/12-security-groups.txt", "Evidence D - inbound rules for each security group")
S += [Spacer(1, 6), table([["Security group", "Inbound rule", "Source", "Reason"],
      ["ewb-sg-bastion", "SSH / TCP 22", "my public IP /32", "Only I can reach the bastion"], ["ewb-sg-app-a", "SSH / TCP 22", "10.10.1.10/32", "Admin only via bastion"],
      ["ewb-sg-app-a", "ICMP Echo request (type 8)", "10.20.1.10/32", "Ping from App-B only"], ["ewb-sg-app-b", "SSH / TCP 22", "10.10.1.10/32", "App-B sees the bastion's private IP as source"],
      ["ewb-sg-app-b", "ICMP Echo request (type 8)", "10.10.2.10/32", "Ping from App-A only"]], [32*mm, 42*mm, 34*mm, 66*mm]),
      Spacer(1, 4), P("Security groups are stateful, so replies to permitted traffic are allowed automatically. Outbound stays at the default allow-all. Network ACLs are the default allow-all.", SM)]
S += [Spacer(1, 6)] + code("evidence/13-instances.txt", "Evidence E - instance inventory") + [PageBreak()]

# 5 Tests
S += [P("6. Test evidence", H1)]
S += code("evidence/20-test01-baseline.txt", "Test 01 - Baseline, BEFORE peering (App-A pings App-B)", "No replies / 100% packet loss. With no peering and no route, VPC A cannot reach 10.20.1.10.")
S += [Spacer(1, 8)] + code("evidence/21-test02-forward.txt", "Test 02 - Forward path AFTER peering and routes (App-A to App-B)", "4 replies, 0% packet loss.")
S += [PageBreak()] + code("evidence/22-test03-reverse.txt", "Test 03 - Reverse path (App-B to App-A)", "4 replies, 0% packet loss. Proves the return route works in both directions.")
S += [Spacer(1, 8)] + code("evidence/23-test04-ssh-appb.txt", "Test 04 - Private SSH to App-B through the bastion", "Shell on App-B reached via ProxyJump. App-B has no public IP.")
S += [Spacer(1, 8)] + code("evidence/24-test05-isolation.txt", "Test 05 - Isolation: no public IPv4 on either application host", "App-A and App-B show None. Only the bastion is public.") + [PageBreak()]

# 6 Failure
S += [P("7. Controlled failure and recovery", H1)]
S += code("evidence/25-controlled-failure.txt", "Evidence - ICMP rule removed from ewb-sg-app-b, tested, restored, tested")
S += [Spacer(1, 6), callout("<b>Explanation.</b> The peering connection and both routes were never changed, yet the ping stopped as soon as the ICMP Echo rule was removed from the destination security group. "
      "This shows that an Active peering is only the link: the security group at App-B still decides whether packets are accepted. Restoring the exact rule (ICMP type 8 from 10.10.2.10/32) brought replies back. The SSH rule stayed in place throughout."), PageBreak()]

# 7 Paths + viva
S += [P("8. Forward path and return path", H1),
      P("<b>Forward path (App-A to App-B).</b> App-A (10.10.2.10) sends a packet to 10.20.1.10. The route table of ewb-a-private has 10.20.0.0/16 pointing to the peering connection, so the packet crosses the peering link into VPC B. "
        "The security group ewb-sg-app-b allows ICMP echo request from 10.10.2.10/32, so App-B accepts it."), Spacer(1, 4),
      P("<b>Return path (App-B to App-A).</b> App-B replies to 10.10.2.10. The route table of ewb-b-private has 10.10.0.0/16 pointing to the same peering connection, so the reply goes back. "
        "Because security groups are stateful, the reply is allowed automatically. Without this return route the request would arrive but the reply would be dropped."), Spacer(1, 4),
      P("<b>Administration path.</b> Laptop -> internet gateway -> bastion (10.10.1.10) -> App-A or App-B. The bastion opens a second SSH connection, which is why the public subnet also needs a route to 10.20.0.0/16 through the peering connection and why App-B's SSH rule uses the bastion's private IP as source. The private key never leaves my laptop."),
      P("9. Viva questions", H1)]
for q, a in [("Why is the return route needed?", "Traffic is two-way. A request can reach the other VPC, but the reply needs a route back to the sender's CIDR. Each VPC's route table must point the other VPC's CIDR at the peering connection."),
             ("Why is the App-B SSH source the bastion's private IP?", "With ProxyJump the bastion opens a new SSH connection to App-B. App-B therefore sees the bastion's private IP (10.10.1.10) as the source, not my laptop's public IP."),
             ("Why does Active peering not guarantee a successful ping?", "Peering only creates the link. Route tables must send traffic into it from both sides, and security groups (and network ACLs) must allow the traffic at the destination."),
             ("Can VPC B use VPC A's internet gateway over peering?", "No. VPC peering does not support edge-to-edge routing, so VPC B cannot use VPC A's internet gateway. Peering is also one-to-one and non-transitive: A-B plus A-C does not create B-C connectivity.")]:
    S += [KeepTogether([P(f"<b>Q. {q}</b>", B), P(a, B), Spacer(1, 5)])]

# 8 Cleanup
S += [PageBreak(), P("10. Cleanup evidence", H1)]
S += code("evidence/30-cleanup.txt", "Cleanup log and verification (all lists blank = nothing left in the account)")
notes = (rd("my_notes.txt") or "").strip() or ("I learned how two private networks are joined with VPC peering, and that a working connection needs three things together: an Active peering, routes on both sides, and matching security group rules. "
        "Non-overlapping CIDRs are mandatory. A bastion lets me administer private servers without giving them public IPs or copying keys onto them. "
        "Testing a failure before and after the change is the best way to prove each component does a real job. Cleaning up promptly avoids surprise charges.")
S += [P("11. What I learned", H1), P(esc(notes).replace("\n", "<br/>"))]

# Screenshots appendix
shots = sorted(glob.glob(os.path.join(HERE, "screenshots", "*.png")) + glob.glob(os.path.join(HERE, "screenshots", "*.jpg")) + glob.glob(os.path.join(HERE, "screenshots", "*.jpeg")))
if shots:
    S += [PageBreak(), P("Appendix: AWS console screenshots", H1)]
    for p in shots:
        try:
            from reportlab.lib.utils import ImageReader
            iw, ih = ImageReader(p).getSize(); mw, mh = 170*mm, 105*mm; r = min(mw/iw, mh/ih)
            cap = os.path.splitext(os.path.basename(p))[0].replace("-", " ").replace("_", " ")
            S += [KeepTogether([P(cap, CAP), Image(p, iw*r, ih*r), Spacer(1, 8)])]
        except Exception as e: print("skip", p, e)
doc.build(S)
print("Report written:", OUT)
missing = [f for f in ["20-test01-baseline","21-test02-forward","22-test03-reverse","23-test04-ssh-appb","24-test05-isolation","25-controlled-failure","10-inventory-vpcs-subnets","11-route-tables","12-security-groups","14-peering","30-cleanup"] if not os.path.exists(os.path.join(HERE, "evidence", f+".txt"))]
if missing: print("Still missing evidence:", ", ".join(missing))
