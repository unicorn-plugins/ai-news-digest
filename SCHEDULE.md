# AI News Digest 스케줄링 설정

## 자동 실행 설정 방법

### 1. Cron Job 설정 (macOS/Linux)

매일 오전 8시에 자동 실행되도록 cron job을 설정합니다.

#### 단계별 설정

1. **cron 편집기 열기**
```bash
crontab -e
```

2. **다음 라인 추가** (매일 오전 8시 실행)
```cron
0 8 * * * /Users/dreamondal/workspace/ai-news-digest/run-daily-digest.sh >> /Users/dreamondal/workspace/ai-news-digest/logs/cron.log 2>&1
```

3. **저장 후 종료** (vi 에디터: `ESC` → `:wq`)

4. **설정 확인**
```bash
crontab -l
```

#### Cron 시간 형식 설명

```
* * * * * 명령어
│ │ │ │ │
│ │ │ │ └─── 요일 (0-7, 0과 7은 일요일)
│ │ │ └───── 월 (1-12)
│ │ └─────── 일 (1-31)
│ └───────── 시 (0-23)
└─────────── 분 (0-59)
```

#### 다양한 스케줄 예시

| 스케줄 | Cron 표현식 | 설명 |
|--------|-------------|------|
| 매일 오전 8시 | `0 8 * * *` | 기본 설정 |
| 평일 오전 9시 | `0 9 * * 1-5` | 월~금 |
| 매 6시간마다 | `0 */6 * * *` | 0시, 6시, 12시, 18시 |
| 매일 오전 8시, 오후 5시 | `0 8,17 * * *` | 하루 2회 |
| 매주 월요일 오전 8시 | `0 8 * * 1` | 주간 다이제스트 |

### 2. macOS LaunchAgent 설정 (권장)

macOS에서는 cron보다 LaunchAgent가 더 안정적입니다.

1. **LaunchAgent 파일 생성**
```bash
cat > ~/Library/LaunchAgents/com.aiNewsDigest.daily.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aiNewsDigest.daily</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/dreamondal/workspace/ai-news-digest/run-daily-digest.sh</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/Users/dreamondal/workspace/ai-news-digest/logs/launchd-stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/dreamondal/workspace/ai-news-digest/logs/launchd-stderr.log</string>

    <key>WorkingDirectory</key>
    <string>/Users/dreamondal/workspace/ai-news-digest</string>

    <key>RunAtLoad</key>
    <false/>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF
```

2. **LaunchAgent 로드**
```bash
launchctl load ~/Library/LaunchAgents/com.aiNewsDigest.daily.plist
```

3. **상태 확인**
```bash
launchctl list | grep aiNewsDigest
```

4. **수동 실행 테스트**
```bash
launchctl start com.aiNewsDigest.daily
```

5. **비활성화 (필요 시)**
```bash
launchctl unload ~/Library/LaunchAgents/com.aiNewsDigest.daily.plist
```

### 3. 수동 실행

스케줄 설정 전 테스트하거나 즉시 실행이 필요한 경우:

```bash
cd /Users/dreamondal/workspace/ai-news-digest
./run-daily-digest.sh
```

## 로그 확인

### 실행 로그 위치
```bash
# 일별 실행 로그
ls -lh /Users/dreamondal/workspace/ai-news-digest/logs/daily-digest-*.log

# 최신 로그 확인
tail -f /Users/dreamondal/workspace/ai-news-digest/logs/daily-digest-*.log

# Cron 로그 (cron 사용 시)
tail -f /Users/dreamondal/workspace/ai-news-digest/logs/cron.log

# LaunchAgent 로그 (LaunchAgent 사용 시)
tail -f /Users/dreamondal/workspace/ai-news-digest/logs/launchd-stdout.log
tail -f /Users/dreamondal/workspace/ai-news-digest/logs/launchd-stderr.log
```

### 로그 관리

오래된 로그 자동 삭제 (30일 이상):
```bash
find /Users/dreamondal/workspace/ai-news-digest/logs -name "daily-digest-*.log" -mtime +30 -delete
```

이를 cron에 추가하려면:
```cron
0 2 * * 0 find /Users/dreamondal/workspace/ai-news-digest/logs -name "daily-digest-*.log" -mtime +30 -delete
```

## 트러블슈팅

### 문제: Cron job이 실행되지 않음

1. **Cron 서비스 상태 확인**
```bash
ps aux | grep cron
```

2. **시스템 로그 확인**
```bash
tail -f /var/log/system.log | grep cron
```

3. **전체 경로 사용** (환경 변수 문제 회피)
```cron
0 8 * * * /bin/bash /Users/dreamondal/workspace/ai-news-digest/run-daily-digest.sh
```

### 문제: Python 모듈을 찾을 수 없음

스크립트가 가상환경을 올바르게 활성화하는지 확인:
```bash
which python3  # 가상환경 경로 확인
```

### 문제: 권한 오류

실행 권한 확인 및 부여:
```bash
chmod +x /Users/dreamondal/workspace/ai-news-digest/run-daily-digest.sh
```

### 문제: Docker 컨테이너 연결 실패

PostgreSQL 컨테이너가 실행 중인지 확인:
```bash
docker ps | grep ai-news-digest
docker-compose -f /Users/dreamondal/workspace/ai-news-digest/docker-compose.yml up -d
```

## 알림 설정

### 에러 알림

스크립트에 이미 에러 발생 시 관리자 이메일 알림 기능이 포함되어 있습니다.
(`tools/customs/apps/email_sender.py`의 `send_error_notification()` 사용)

### 성공 알림 (선택)

매일 실행 성공 시에도 알림을 받고 싶다면:

`run-daily-digest.sh` 마지막에 추가:
```bash
if [ $EXIT_CODE -eq 0 ]; then
    echo "뉴스레터 발행 성공" | mail -s "AI News Digest - Success" your-email@example.com
fi
```

## 모니터링 대시보드

실행 상태를 웹에서 확인하고 싶다면:

1. **간단한 상태 페이지**
```bash
python3 -m http.server 8000 --directory /Users/dreamondal/workspace/ai-news-digest/logs
```

2. **브라우저에서 접속**
```
http://localhost:8000
```

## 추천 설정

**초보자**: LaunchAgent (macOS) 또는 systemd timer (Linux)
**숙련자**: Cron + 로그 로테이션
**프로덕션**: Kubernetes CronJob 또는 AWS EventBridge

---

## 빠른 시작

```bash
# 1. LaunchAgent 설정 (macOS)
curl -o ~/Library/LaunchAgents/com.aiNewsDigest.daily.plist \
  https://raw.githubusercontent.com/yourusername/ai-news-digest/main/examples/launchd.plist

launchctl load ~/Library/LaunchAgents/com.aiNewsDigest.daily.plist

# 2. 또는 Cron 설정 (Linux/macOS)
(crontab -l 2>/dev/null; echo "0 8 * * * /Users/dreamondal/workspace/ai-news-digest/run-daily-digest.sh >> /Users/dreamondal/workspace/ai-news-digest/logs/cron.log 2>&1") | crontab -

# 3. 즉시 테스트 실행
/Users/dreamondal/workspace/ai-news-digest/run-daily-digest.sh
```

설정 완료! 🎉
