#!/bin/bash

# AI News Digest - 자동 스케줄링 설정 도우미

set -e

PROJECT_DIR="/Users/dreamondal/workspace/ai-news-digest"
SCRIPT_PATH="$PROJECT_DIR/run-daily-digest.sh"

echo "=========================================="
echo "AI News Digest - 스케줄링 설정"
echo "=========================================="
echo ""

# OS 확인
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
else
    OS="Unknown"
fi

echo "🖥️  감지된 OS: $OS"
echo ""

# 스크립트 실행 권한 확인
if [ ! -x "$SCRIPT_PATH" ]; then
    echo "⚠️  실행 권한 부여 중..."
    chmod +x "$SCRIPT_PATH"
fi

# 로그 디렉토리 생성
mkdir -p "$PROJECT_DIR/logs"

echo "다음 중 선택하세요:"
echo ""
echo "1) Cron Job 설정 (모든 OS, 간단)"
echo "2) LaunchAgent 설정 (macOS 전용, 권장)"
echo "3) 수동 실행 테스트"
echo "4) 기존 스케줄 확인"
echo "5) 스케줄 제거"
echo ""
read -p "선택 (1-5): " choice

case $choice in
    1)
        echo ""
        echo "📅 Cron Job 설정"
        echo "매일 오전 8시에 실행됩니다."
        echo ""

        CRON_LINE="0 8 * * * $SCRIPT_PATH >> $PROJECT_DIR/logs/cron.log 2>&1"

        # 기존 cron에 이미 있는지 확인
        if crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH"; then
            echo "⚠️  이미 cron에 등록되어 있습니다."
            echo ""
            crontab -l | grep "$SCRIPT_PATH"
            echo ""
            read -p "기존 설정을 유지하시겠습니까? (y/n): " keep
            if [[ "$keep" != "y" ]]; then
                # 기존 항목 제거 후 새로 추가
                (crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH"; echo "$CRON_LINE") | crontab -
                echo "✅ Cron 설정 업데이트 완료!"
            fi
        else
            # 새로 추가
            (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
            echo "✅ Cron 설정 완료!"
        fi

        echo ""
        echo "현재 cron 설정:"
        crontab -l | grep "$SCRIPT_PATH" || echo "(없음)"
        ;;

    2)
        if [[ "$OS" != "macOS" ]]; then
            echo "❌ LaunchAgent는 macOS 전용입니다."
            exit 1
        fi

        echo ""
        echo "📅 LaunchAgent 설정"
        echo "매일 오전 8시에 실행됩니다."
        echo ""

        PLIST_FILE="$HOME/Library/LaunchAgents/com.aiNewsDigest.daily.plist"

        cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aiNewsDigest.daily</string>

    <key>ProgramArguments</key>
    <array>
        <string>$SCRIPT_PATH</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/launchd-stdout.log</string>

    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/launchd-stderr.log</string>

    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>

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

        # 기존 설정 언로드 (에러 무시)
        launchctl unload "$PLIST_FILE" 2>/dev/null || true

        # 새 설정 로드
        launchctl load "$PLIST_FILE"

        echo "✅ LaunchAgent 설정 완료!"
        echo ""
        echo "상태 확인:"
        launchctl list | grep aiNewsDigest || echo "(로드됨, 대기 중)"
        echo ""
        echo "수동 실행 테스트:"
        echo "  launchctl start com.aiNewsDigest.daily"
        ;;

    3)
        echo ""
        echo "🧪 수동 실행 테스트"
        echo ""

        read -p "지금 실행하시겠습니까? (y/n): " confirm
        if [[ "$confirm" == "y" ]]; then
            echo ""
            echo "실행 중..."
            "$SCRIPT_PATH"
        else
            echo "취소됨"
        fi
        ;;

    4)
        echo ""
        echo "📋 기존 스케줄 확인"
        echo ""

        echo "--- Cron Jobs ---"
        crontab -l 2>/dev/null | grep "$SCRIPT_PATH" || echo "(없음)"
        echo ""

        if [[ "$OS" == "macOS" ]]; then
            echo "--- LaunchAgents ---"
            launchctl list | grep aiNewsDigest || echo "(없음)"
            echo ""

            PLIST_FILE="$HOME/Library/LaunchAgents/com.aiNewsDigest.daily.plist"
            if [ -f "$PLIST_FILE" ]; then
                echo "LaunchAgent 파일:"
                echo "  $PLIST_FILE"
                echo ""
                echo "다음 실행 시간:"
                grep -A2 "StartCalendarInterval" "$PLIST_FILE" | grep -E "Hour|Minute"
            fi
        fi
        ;;

    5)
        echo ""
        echo "🗑️  스케줄 제거"
        echo ""

        read -p "정말 모든 스케줄을 제거하시겠습니까? (y/n): " confirm
        if [[ "$confirm" != "y" ]]; then
            echo "취소됨"
            exit 0
        fi

        # Cron 제거
        if crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH"; then
            crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH" | crontab -
            echo "✅ Cron Job 제거 완료"
        fi

        # LaunchAgent 제거 (macOS)
        if [[ "$OS" == "macOS" ]]; then
            PLIST_FILE="$HOME/Library/LaunchAgents/com.aiNewsDigest.daily.plist"
            if [ -f "$PLIST_FILE" ]; then
                launchctl unload "$PLIST_FILE" 2>/dev/null || true
                rm "$PLIST_FILE"
                echo "✅ LaunchAgent 제거 완료"
            fi
        fi

        echo ""
        echo "모든 스케줄이 제거되었습니다."
        ;;

    *)
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "완료! 상세 정보는 SCHEDULE.md 참고"
echo "=========================================="
