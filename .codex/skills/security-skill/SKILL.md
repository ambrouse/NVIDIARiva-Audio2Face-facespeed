---
name: security-skill
description: "Quy tắc bắt buộc khi thiết kế, review hoặc kiểm thử bảo mật production."
argument-hint: "security task"
user-invocable: true
---

# Security Skill

Áp dụng khi task chạm auth, permission, dữ liệu nhạy cảm, API/backend, frontend security, dependency, config, hạ tầng, logging, production readiness hoặc security review.

## Baseline

- Dùng OWASP ASVS, OWASP Top 10 và OWASP Cheat Sheet làm chuẩn tham chiếu khi phù hợp.
- Không tuyên bố secure/production-ready nếu chưa có evidence từ review, test và config môi trường.
- Finding nên có severity, affected area, evidence, impact, exploit condition, remediation, verification và residual risk.
- Critical/High exploitable phải fix trước khi gọi ready, trừ khi user chấp nhận risk rõ ràng.

## Quy Trình

1. Xác định asset, actor, quyền, entry point, trust boundary, dữ liệu nhạy cảm và abuse case thực tế.
2. Kiểm từng lớp: frontend, API/backend, service, database, dependency, config, deployment, logging/monitoring.
3. Áp dụng deny-by-default, least privilege, explicit allowlist và secure defaults.
4. Viết hoặc đề xuất test bảo mật cho authz, validation, injection, XSS, CSRF, secrets, error leakage và config critical.
5. Kiểm không đưa secret/PII vào code, test, docs, logs, snapshot, report hoặc commit.
6. Nếu có log/docs, dùng `logging-skill`/`documentation-skill` và redact dữ liệu nhạy cảm.

## Auth, Session Và Authorization

- Không tự viết crypto/password hashing nếu framework/library chuẩn đã có; password dùng Argon2id/bcrypt/scrypt với cost phù hợp.
- Token reset/invite/recovery phải có expiry, one-time use, storage an toàn và chống enumeration/reuse.
- Cookie session production nên có `HttpOnly`, `Secure`, `SameSite` phù hợp, domain/path tối thiểu.
- JWT phải verify signature, issuer, audience, expiry; không tin payload chưa verify.
- Authorization enforce ở backend, không chỉ ẩn UI; kiểm owner, role, scope, tenant, organization và resource state.

## Input, Output Và Dữ Liệu

- Validate tại boundary: HTTP request, form, CLI arg, webhook, file upload, queue, external API.
- Dùng schema/DTO allowlist; kiểm type, length, format, range, enum, encoding, size limit và mass-assignment risk.
- Query/command/template phải dùng API an toàn: parameterized query, ORM safe API, argument array, allowlist hoặc context-aware escaping.
- Không dùng raw HTML/dangerouslySetInnerHTML nếu chưa sanitize bằng allowlist và test payload XSS.
- Thu thập dữ liệu tối thiểu; mask/redact PII trong logs, analytics, error reporting.

## Secrets, Dependency Và Supply Chain

- Không commit `.env`, private key, token, credential, database URL thật hoặc cloud secret.
- `.env.example` chỉ chứa placeholder an toàn.
- Nếu phát hiện secret lộ, đề xuất rotate/revoke và xử lý history theo quy trình user duyệt.
- Chỉ thêm dependency khi lợi ích rõ; kiểm license, maintenance, release cadence và vulnerability.
- CI token dùng least privilege; untrusted PR không được nhận secret nguy hiểm.

## Config, Infra Và Logging

- Production phải bật TLS, debug off, default credential bị chặn/đổi.
- CORS phải allowlist origin cụ thể; không dùng wildcard với credentials.
- Public error không lộ stack trace, SQL, internal URL, token hoặc secret.
- Audit log quan trọng: login fail nhiều lần, reset password, permission denied critical, admin action, token revoke, webhook verify fail.
- Không log token, password, session ID, authorization header, PII hoặc payload nhạy cảm.

## Không Được Làm

- Không hardcode secret, bypass auth/permission production, nối chuỗi SQL/command/template nguy hiểm.
- Không thêm dependency không rõ nguồn gốc hoặc tắt security check/hook/linter/scan/TLS verification nếu user chưa yêu cầu rõ.
- Không hướng dẫn phá hoại, DoS, credential abuse, evasion hoặc mass targeting.
