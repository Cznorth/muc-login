#!/usr/bin/env python3
"""
MUC CAS Login (ca.muc.edu.cn)

中央民族大学统一身份认证 CAS 登录模块
Keywords: 中央民族大学 MUC 统一身份认证 CAS SSO 单点登录 国密 SM2 加密 py_mini_racer

Uses py_mini_racer (in-process V8) to run the original browser SM2 library for encryption.
"""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import requests
import py_mini_racer

LOGIN_URL = "https://ca.muc.edu.cn/zfca/login"
SERVICE = "http://my.muc.edu.cn/user/simpleSSOLogin"

SM2_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sm2.min.js")
PUBKEY = "BMgXvoCLbC9cF8JAS/bv6Gd82+K+fFC2nRi7QJO3GvDkx0iLBmqDMpQUBxjC3yTfXN83cPVZRplPDsvr92K4omA="


def sm2_encrypt(password):
    """Use py_mini_racer + browser's original sm2.min.js to encrypt (no Node.js needed)"""
    ctx = py_mini_racer.MiniRacer()
    ctx.eval("""var window = this;
var navigator = { userAgent: 'py_mini_racer' };
var btoa = function(s) {
    var chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
    var result='',i=0;
    while(i<s.length){
        var c1=s.charCodeAt(i++);
        if(i<s.length){var c2=s.charCodeAt(i++);
        if(i<s.length){var c3=s.charCodeAt(i++);
            result+=chars.charAt(c1>>2)+chars.charAt(((c1&3)<<4)|(c2>>4))+chars.charAt(((c2&15)<<2)|(c3>>6))+chars.charAt(c3&63);
        }else{result+=chars.charAt(c1>>2)+chars.charAt(((c1&3)<<4)|(c2>>4))+chars.charAt(((c2&15)<<2))+'=';}
        }else{result+=chars.charAt(c1>>2)+chars.charAt(((c1&3)<<4))+'==';}
    }
    return result;
};
var atob = function(s) {
    var chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
    var result='',i=0;
    s=s.replace(/[^A-Za-z0-9+/=]/g,'');
    while(i<s.length){
        var c1=chars.indexOf(s.charAt(i++));
        var c2=chars.indexOf(s.charAt(i++));
        var c3=chars.indexOf(s.charAt(i++));
        var c4=chars.indexOf(s.charAt(i++));
        result+=String.fromCharCode((c1<<2)|(c2>>4));
        if(c3!==64)result+=String.fromCharCode(((c2&15)<<4)|(c3>>2));
        if(c4!==64)result+=String.fromCharCode(((c3&3)<<6)|c4);
    }
    return result;
};""")
    with open(SM2_PATH, 'r', encoding='utf-8') as f:
        ctx.eval(f.read())
    return ctx.eval(f'sm2.encrypt({json.dumps(password)}, {json.dumps(PUBKEY)})')


def login(username, password, verbose=True):
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })

    full_url = f"{LOGIN_URL}?service={requests.utils.quote(SERVICE, safe='')}"

    # Get login page + flowId
    if verbose:
        print(f"[1] GET login page...")
    r = s.get(full_url, timeout=15)
    r.encoding = "utf-8"
    flow_id = re.search(r'<input\s+name="flowId"\s+value="([^"]+)"', r.text)
    if not flow_id:
        print("ERROR: No flowId found in page")
        return None
    flow_id = flow_id.group(1)
    if verbose:
        print(f"    flowId = {flow_id}")
        print(f"    JSESSIONID = {s.cookies.get('JSESSIONID','N/A')[:25]}")

    # Encrypt password via py_mini_racer
    if verbose:
        print(f"[2] SM2 encrypt...")
    enc_pwd = sm2_encrypt(password)
    if verbose:
        print(f"    encrypted len = {len(enc_pwd)}")

    # POST login
    data = {
        "username": username,
        "password": enc_pwd,
        "loginType": "username_password",
        "flowId": flow_id,
        "captcha": "",
        "delegator": "",
        "tokenCode": "",
        "continue": "",
        "asserts": "",
        "pageFrom": "",
        "submit": "\u767b\u5f55",
    }

    if verbose:
        print(f"[3] POST login...")
    r2 = s.post(full_url, data=data, allow_redirects=False, timeout=30)
    r2.encoding = "utf-8"

    if verbose:
        print(f"    status = {r2.status_code}")
        print(f"    Location = {r2.headers.get('Location', '(none)')}")

    if r2.status_code in (302, 301):
        loc = r2.headers["Location"]
        if verbose:
            print(f"[4] Follow -> {loc[:80]}...")
        r3 = s.get(loc, allow_redirects=True, timeout=15)
        r3.encoding = "utf-8"
        if verbose:
            print(f"    Final URL = {r3.url[:80]}")
            print(f"    Status = {r3.status_code}")
            if "my.muc.edu.cn" in r3.url and r3.status_code == 200:
                title = re.search(r'<title>([^<]+)', r3.text)
                print(f"    Title = {title.group(1) if title else '(none)'}")
                print(f"\n[OK] Login successful!")
                print(f"\nCookies:")
                for c in s.cookies:
                    print(f"  {c.name} = {c.value[:60]}{'...' if len(c.value)>60 else ''}")
            elif "ticket=" in r3.url:
                print(f"    Got ticket, redirected to CAS")
            else:
                body = re.sub(r'<script[^>]*>.*?</script>', '', r3.text, flags=re.DOTALL)
                body = re.sub(r'<[^>]+>', ' ', body)
                body = re.sub(r'\s+', ' ', body).strip()
                print(f"    Response: {body[:200]}")
        return s, r3
    else:
        if verbose:
            print(f"[FAIL] Login failed")
            # Check for slider captcha or other requirements
            body = re.sub(r'<script[^>]*>.*?</script>', '', r2.text, flags=re.DOTALL)
            body = re.sub(r'<[^>]+>', ' ', body)
            body = re.sub(r'\s+', ' ', body).strip()
            # Find error hints
            hints = re.findall(r'(密码错误|验证码|滑块|失败|错误|锁定|冻结|不存在|未找到)', body)
            if hints:
                print(f"    Error hints: {', '.join(set(hints))}")
            print(f"    Body snippet: {body[:200]}")
        return s, r2


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python login.py <username> <password>")
        sys.exit(1)
    session, resp = login(sys.argv[1], sys.argv[2], verbose=True)

    if session and "my.muc.edu.cn" in (resp.url if resp else ""):
        print("\n=== Verify: my.muc.edu.cn ===")
        r = session.get("https://my.muc.edu.cn/page/11", timeout=15)
        r.encoding = "utf-8"
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            body = re.sub(r'<[^>]+>', ' ', r.text)
            body = re.sub(r'\s+', ' ', body).strip()
            print(f"  Body: {body[:200]}")
