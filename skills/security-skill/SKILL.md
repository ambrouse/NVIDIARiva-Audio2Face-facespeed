---
name: security-skill
description: Quy tắc bắt buộc khi thiết kế, viết, review hoặc kiểm thử bảo mật production cho frontend, backend, API, config, dependency và vận hành.
argument-hint: "security task"
user-invocable: true
---

# Security Skill

Áp dụng khi task chạm auth, permission, dữ liệu nhạy cảm, API/backend, frontend security, dependency, config, hạ tầng, logging, production readiness hoặc security review.

## Baseline
- Dùng OWASP ASVS, OWASP Top 10 và OWASP Cheat Sheet làm chuẩn tham chiếu.
- Không tuyên bố secure/production-ready nếu chưa có evidence từ review, test và config môi trường.
- Finding nên có severity, affected area, evidence, impact, exploit condition, remediation, verification và residual risk.
- Critical/High exploitable phải fix trước khi gọi ready, trừ khi user chấp nhận risk rõ ràng.

## Quy trình bắt buộc
1. Xác định asset, actor, quyền, entry point, trust boundary, dữ liệu nhạy cảm và abuse case thực tế.
2. Kiểm từng lớp: frontend, API/backend, service, database, dependency, config, deployment, logging/monitoring.
3. Áp dụng deny-by-default, least privilege, explicit allowlist và secure defaults.
4. Viết hoặc đề xuất test bảo mật cho authz, validation, injection, XSS, CSRF, secrets, error leakage và config critical.
5. Kiểm không đưa secret/PII vào code, test, docs, logs, snapshot, report hoặc commit.
6. Nếu có log/docs, dùng `logging-skill`/`documentation-skill` và redaction dữ liệu nhạy cảm.

## Auth, session và authorization
- Không tự viết crypto/password hashing nếu framework/library chuẩn đã có; password dùng Argon2id/bcrypt/scrypt với cost phù hợp.
- Reset/invite/recovery token phải có expiry, one-time use, storage an toàn và chống enumeration/reuse.
- Cookie session production nên `HttpOnly`, `Secure`, `SameSite` phù hợp, domain/path tối thiểu.
- JWT phải verify signature, issuer, audience, expiry; không tin payload chưa verify.
- Không lưu access token nhạy cảm trong localStorage nếu có lựa chọn session cookie an toàn hơn.
- Authorization enforce ở backend, không chỉ ẩn UI; kiểm owner, role, scope, tenant, organization và resource state.
- Admin/superuser path cần guard riêng và audit log.

## Input, output và dữ liệu
- Validate tại boundary: HTTP request, form, CLI arg, webhook, file upload, queue, external API.
- Dùng schema/DTO allowlist; kiểm type, length, format, range, enum, encoding, size limit và mass-assignment risk.
- Query/command/template phải dùng API an toàn: parameterized query/ORM safe API, argument array/allowlist, context-aware escaping.
- Không dùng raw HTML/dangerouslySetInnerHTML nếu chưa sanitize bằng allowlist và test payload XSS.
- File upload phải kiểm MIME thực tế, extension allowlist, size limit, path an toàn và scan nếu production yêu cầu.
- Thu thập dữ liệu tối thiểu; mask/redact PII trong logs, analytics, error reporting; retention/deletion phải rõ khi xử lý dữ liệu người dùng.

## Backend/API
- Mutating endpoint phải có authentication, authorization, validation, CSRF protection nếu dùng cookie session và rate limit/audit log nếu nhạy cảm.
- Public error không lộ stack trace, SQL, internal URL, token hoặc secret.
- CORS phải allowlist origin cụ thể; không dùng wildcard với credentials.
- Database user dùng least privilege; migration critical cần tránh mất/lộ dữ liệu và có rollback plan.
- Multi-tenant query phải enforce tenant scope ở mọi access path.
- Webhook phải verify signature, timestamp/nonce, chống replay và xử lý duplicate/idempotency khi phù hợp.
- Auth, permission, payment, quota, compliance phải fail closed.

## Frontend/browser
- Không tin client-side check cho security enforcement.
- Không expose secret trong frontend bundle, public env, source map hoặc console log.
- Tránh `eval`, `new Function`, string-based timer và direct DOM injection với input không tin cậy.
- URL từ user phải validate scheme; chặn `javascript:` và scheme nguy hiểm.
- External link mở tab mới nên dùng `rel="noopener noreferrer"` khi phù hợp.
- CSP/security headers là lớp phòng thủ bổ sung, không thay thế output encoding.
- Third-party script/package chỉ thêm khi cần thiết, đáng tin và hiểu dữ liệu gửi ra ngoài.

## Secrets, dependency và supply chain
- Không commit `.env`, private key, token, credential, database URL thật hoặc cloud secret; `.env.example` chỉ chứa placeholder an toàn.
- Nếu phát hiện secret lộ, đề xuất rotate/revoke và xử lý history theo quy trình user duyệt.
- Chỉ thêm dependency khi lợi ích rõ; kiểm license, maintenance, popularity, release cadence và vulnerability.
- Không cập nhật hàng loạt ngoài phạm vi task; lockfile chỉ đổi đúng phạm vi.
- CI token dùng least privilege; untrusted PR không được nhận secret nguy hiểm.
- Khuyến nghị SAST/SCA/secret scan/IaC/container scan cho production repo.

## Config, infra và vận hành
- Production phải bật TLS, không tắt certificate verification, debug off, default credential bị chặn/đổi.
- Config dev/staging/prod tách rõ; artifact/source map/error detail nhạy cảm không public nếu không có kiểm soát.
- Security headers phù hợp kiến trúc: CSP, HSTS, X-Content-Type-Options, Referrer-Policy, frame-ancestors/X-Frame-Options.
- Container không bake secret, nên chạy non-root, base image tối giản/cập nhật và scan vulnerability.
- IaC/cloud dùng least privilege; public bucket/database/queue chỉ mở khi có lý do rõ.

## Logging, monitoring và incident
- Security/audit log quan trọng: login fail nhiều lần, reset password, permission denied critical, admin action, token revoke, webhook verify fail.
- Audit log nên có actor, action, target, timestamp, result, correlation ID nếu có; tuyệt đối không log secret/token/password/cookie/auth header/PII không cần thiết.
- Monitor spike 401/403, rate limit hit, webhook failure, admin action bất thường và dependency/service security failure.
- Nếu phát hiện leak/vulnerability nghiêm trọng, dừng mở rộng thay đổi, báo user và đề xuất containment; không tự xóa evidence, force-push hoặc rewrite history khi chưa được duyệt.

## Test/gate bắt buộc khi phù hợp
- Auth matrix: unauthenticated 401, thiếu quyền 403, owner/non-owner, cross-tenant, expired/revoked token.
- Validation/malformed payload, injection payload representative, XSS render path, CSRF nếu cookie session.
- Webhook signature/replay/duplicate, rate limit/brute force cho endpoint nhạy cảm.
- Error response không lộ thông tin nhạy cảm; public env/bundle không chứa secret.
- SAST/SCA/secret scan/DAST/IaC/container scan khi có môi trường và phạm vi phù hợp.

## Không được làm
- Không hardcode secret, bypass auth/permission production, nối chuỗi SQL/command/template nguy hiểm.
- Không log token, password, session ID, authorization header, PII hoặc payload nhạy cảm.
- Không thêm dependency không rõ nguồn gốc hoặc tắt security check/hook/linter/scan/TLS verification nếu user chưa yêu cầu rõ.
- Không hướng dẫn phá hoại, DoS, credential abuse, evasion hoặc mass targeting.
