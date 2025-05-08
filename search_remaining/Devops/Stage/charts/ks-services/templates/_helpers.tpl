{{/*
Expand the name of the chart.
*/}}
{{- define "ks-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "ks-service.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "ks-service.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "ks-service.labels" -}}
helm.sh/chart: {{ include "ks-service.chart" . }}
{{ include "ks-service.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ks-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ks-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app: {{ .Chart.Name }}
version: {{ .Values.deployment.version }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "ks-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "ks-service.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{- define "ks-service.namespace" -}}
{{- default "default" .Values.namespace }}
{{- end}}

{{- define "ks-service.virtualhosts"}}
{{- if .Values.namespace }}
{{- printf "%s.%s.svc.cluster.local" .Release.Name .Values.namespace }}
{{- else }}
{{- include "ks-service.name" . }}
{{- end }}
{{- end }}

{{- define "ks-service.common_secret"}}
{{- printf "common-%s-secret" (include "ks-service.name" .) }}
{{- end }}

{{- define "ks-service.rds_secret"}}
{{- printf "rds-%s-secret" (include "ks-service.name" .) }}
{{- end }}

{{- define "ks-service.common_secret_provider"}}
{{- printf "common-%s-secret" (include "ks-service.name" .) }}
{{- end }}

{{- define "ks-service.rds_secret_provider"}}
{{- printf "rds-%s-secret" (include "ks-service.name" .) }}
{{- end }}

{{- define "ks-service.rds_volume_secrets"}}
{{- printf "rds-%s-vol" (include "ks-service.name" .) }}
{{- end }}

{{- define "ks-service.common_volume_secrets"}}
{{- printf "common-%s-vol" (include "ks-service.name" .) }}
{{- end }}


{{- define "uuidv4" }}
{{- `{{- uuidv4 -}}` }}
{{- end }}


