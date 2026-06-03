# Terraform / Terragrunt 規約

Terraform / Terragrunt + GitOps を使うプロジェクトに適用せよ。

---

## 1. IaC 横展開（全環境同時適用）

### MANDATORY

**アプリリソースまたはインフラモジュールを追加する場合、全環境に同時に追加せよ。1 環境だけに追加して他環境への適用を後回しにするな。**

| 操作 | 全環境への適用 |
|------|-------------|
| GitOps アプリリソース追加（`gitops/apps/<env>/` 等） | stg / prod（またはプロジェクト定義の全環境）に同時追加 |
| Terragrunt モジュール追加（`infra/envs/<env>/` 等） | dev / stg / prod（またはプロジェクト定義の全環境）に同時追加 |

環境ディレクトリの命名はプロジェクトによって異なる。プロジェクトのディレクトリ構造を確認して適用せよ。

**例外**: 段階的ロールアウトが業務要件として明示されている場合のみ許容する。PR に理由を明記し、残り環境への適用 Issue を即時作成せよ。

---

## 2. Terraform validation 必須

### MANDATORY: 新規モジュールの必須変数には `validation` ブロックを定義せよ

```hcl
# DO NOT: 空文字デフォルトで必須チェックを回避するな
variable "cluster_name" {
  type    = string
  default = ""
}

# DO: validation ブロックで明示的に検証せよ
variable "cluster_name" {
  type        = string
  description = "EKS クラスター名"
  validation {
    condition     = length(var.cluster_name) > 0
    error_message = "cluster_name は空文字にできません。"
  }
}
```

**適用範囲**: 新規モジュールの必須変数のみ。既存モジュール修正時は対象外（別途リファクタリング Issue を作成せよ）。

---

## 3. GitOps / Kubernetes 直接操作禁止

**全ての変更は Git を通じてコードで管理せよ。**

### DO NOT（検証目的を除く）

| コマンド | 禁止理由 |
|---------|---------|
| `kubectl apply / delete / patch / edit` | Git に記録されない変更が発生する |
| `helm upgrade / install / uninstall`（CI/CD 外） | GitOps の自動同期と競合する |
| `kubectl exec` 等による実行時設定変更 | 状態がコードに反映されない |

### 許可される例外

| 操作 | 用途 |
|------|------|
| `kubectl get / describe / logs / port-forward` | 読み取り専用 |
| `kubectl diff` / `helm template` / `helm lint` / `helm dry-run` | 検証目的 |
| 緊急インシデント対応 | 事後に**必ず**コードへ反映 + Issue 起票が必要 |

### 変更フロー（この順で行え）

```
Git（単一の真実の源）
  ↓ PR → レビュー → マージ
インフラ層（Terraform+Terragrunt）: CI が terraform apply
k8s マニフェスト層（Helm Chart）:   Flux が自動同期
```

---

## 4. IaC 変更時の必須チェックリスト（毎回確認せよ）

- [ ] **全環境確認**: 追加・変更対象が全環境に存在するか確認し、欠けている環境があれば同一 PR に含めよ
- [ ] **validation 確認**: 新規モジュールの必須変数に `validation` ブロックが定義されているか確認せよ
- [ ] **ドリフト検出**: `terraform plan` の差分に意図しない変更が含まれていないか確認せよ
- [ ] **直接操作禁止**: k8s リソース変更は Helm Chart values または GitOps マニフェスト変更として提案せよ
- [ ] **緊急対応後**: 直接操作した場合はコードへの反映と Issue 起票を必ず行え

---

## 5. ロギング・監査

### MANDATORY

- Terraform の実行ログ（plan / apply）は CI/CD パイプラインで保存する
- `TF_LOG` は CI では `INFO` に設定し、デバッグ時のみ `DEBUG` に変更する
- `terraform apply` の出力（変更件数・リソース名）は Slack または監査ログに転送する

### DO NOT

- `TF_LOG=TRACE` を本番 CI で常時有効にする（認証情報がログに漏れる可能性がある）
