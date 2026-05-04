# 中央民族大学 CAS 登录

> 中央民族大学统一身份认证 | MUC CAS Login | 民大 CAS | 国密 SM2 加密登录

使用 Python 自动化登录中央民族大学 CAS 统一身份认证系统（ca.muc.edu.cn），
获取 SSO 票据（TGC），可用于后续访问校内各系统（如 my.muc.edu.cn）。

**关键词：** 中央民族大学 · MUC · 统一身份认证 · CAS · 单点登录 · 校园网 · 自动化 · Python · 国密 · SM2 加密 · py_mini_racer · SSO · my.muc.edu.cn

## 原理

1. **获取登录页** — 从 CAS 服务获取 `flowId`（防重放令牌）
2. **SM2 加密密码** — 使用浏览器原版 `sm2.min.js` 国密 SM2 加密库，通过 `py_mini_racer`（嵌入式 V8）在 Python 进程内执行
3. **提交登录** — POST 用户名 + SM2 密文 + flowId
4. **跟随重定向** — 获取 `SSO_TGC` Cookie，完成单点登录

## 依赖

```bash
pip install requests py-mini-racer
```

## 使用

```bash
python login.py <学号> <密码>
```

成功后会打印 Cookie 信息（含 SSO_TGC），并自动验证访问 my.muc.edu.cn。

## 文件说明

| 文件 | 说明 |
|------|------|
| `login.py` | 主登录脚本 |
| `sm2.min.js` | 原版国密 SM2 浏览器库（从 CAS 页面提取） |
| `sm2-enc.js` | 已废弃，原 Node.js 封装（sm2.min.js 作为本地文件已内置） |

## 技术细节

- SM2 公钥从 CAS 登录页前端代码中提取
- 加密过程完全在本地执行，密码不离开本机
- 不依赖 Node.js，纯 Python + py_mini_racer 嵌入式 V8 引擎
