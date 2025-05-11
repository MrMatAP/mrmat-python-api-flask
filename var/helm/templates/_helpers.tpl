
{{/* Common labels */}}
{{ define "common.labels" }}
app: mpaflask
version: {{ .Chart.AppVersion }}
app.kubernetes.io/part-of: mpaflask
app.kubernetes.io/version: {{ .Chart.AppVersion }}
{{ end }}
