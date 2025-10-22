#!/bin/bash
# Скрипт для генерации самоподписанных SSL сертификатов для разработки

set -e

CERT_DIR="./certs"
DOMAIN=${1:-localhost}
VALIDITY_DAYS=${2:-365}

echo "🔒 Генерация SSL сертификатов для домена: $DOMAIN"

# Создаем директорию для сертификатов
mkdir -p "$CERT_DIR"

# Генерируем приватный ключ
echo "🔑 Генерация приватного ключа..."
openssl genrsa -out "$CERT_DIR/key.pem" 2048

# Генерируем сертификат
echo "📜 Генерация самоподписанного сертификата..."
openssl req -new -x509 -key "$CERT_DIR/key.pem" -out "$CERT_DIR/cert.pem" -days $VALIDITY_DAYS -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"

# Создаем комбинированный файл (cert + key)
cat "$CERT_DIR/cert.pem" "$CERT_DIR/key.pem" > "$CERT_DIR/combined.pem"

# Устанавливаем правильные права доступа
chmod 600 "$CERT_DIR/key.pem"
chmod 644 "$CERT_DIR/cert.pem"
chmod 600 "$CERT_DIR/combined.pem"

echo "✅ Сертификаты созданы в директории: $CERT_DIR"
echo "📝 Файлы:"
echo "   - Сертификат: $CERT_DIR/cert.pem"
echo "   - Приватный ключ: $CERT_DIR/key.pem"
echo "   - Комбинированный: $CERT_DIR/combined.pem"
echo ""
echo "⚠️  Это самоподписанные сертификаты для разработки!"
echo "   Для production используйте сертификаты от доверенного CA (Let's Encrypt, Cloudflare, и т.д.)"
echo ""
echo "🚀 Для включения HTTPS в docker-compose:"
echo "   export HTTPS_ENABLED=true"
echo "   export FORCE_HTTPS=true"
echo "   docker-compose up"