@echo off
cd D:\callagente
go build ./cmd/server
echo BUILD EXIT CODE: %ERRORLEVEL%
