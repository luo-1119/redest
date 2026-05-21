if ! command -v java &> /dev/null; then
    echo "java未安装"
    pkg install openjdk-21 -y
fi