{{/*
Expand the default name of the resource based on release name and chart name.
*/}}
{{- define "ks-service-batchjob.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else }}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end }}
{{- end }}

{{/*
Generate a default label for all resources based on the chart name.
*/}}
{{- define "ks-service-batchjob.labels" -}}
app.kubernetes.io/name: {{ include "ks-service-batchjob.name" . }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Generate a default name for the container.
*/}}
{{- define "ks-service-batchjob.containername" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{/*
Generate a list of environment variables from secrets.
*/}}
{{- define "ks-service-batchjob.envSecrets" -}}
{{- range .Values.envSecrets }}
- secretRef:
    name: {{ .name }}
{{- end }}
{{- end }}

{{/*
Generate a list of image pull secrets.
*/}}
{{- define "ks-service-batchjob.imagePullSecrets" -}}
{{- range .Values.imagePullSecrets }}
- name: {{ .name }}
{{- end }}
{{- end }}

{{/*
Generate a list of volumes.
*/}}
{{- define "ks-service-batchjob.volumes" -}}
{{- range .Values.volumes }}
- name: {{ .name }}
  emptyDir: {}
{{- end }}
{{- end }}


