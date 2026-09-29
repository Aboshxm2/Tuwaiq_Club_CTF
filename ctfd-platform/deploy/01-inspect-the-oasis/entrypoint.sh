#!/bin/sh
# Build the site from the team's flag, then hand off to nginx.
# whale passes the flag as FLAG. Split it into three parts and hide one part
# in each of the three source files, exactly like the file-based version.
set -eu

# Note: don't use ${FLAG:-default} with a brace-containing default — the braces
# break the parameter expansion and append a stray '}' to a real flag.
if [ -z "${FLAG:-}" ]; then
  FLAG='TAIBAH{local_test_flag_for_challenge_01}'
fi

len=${#FLAG}
a=$((len / 3))
b=$((2 * len / 3))
p1=$(printf '%s' "$FLAG" | cut -c "1-${a}")
p2=$(printf '%s' "$FLAG" | cut -c "$((a + 1))-${b}")
p3=$(printf '%s' "$FLAG" | cut -c "$((b + 1))-${len}")

root=/usr/share/nginx/html
mkdir -p "$root"

cat > "$root/index.html" <<HTML
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Oasis Travel Agency</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header>
    <h1>Oasis Travel Agency</h1>
    <p>Your journey through the desert starts here.</p>
  </header>
  <main>
    <h2>Our Tours</h2>
    <ul>
      <li>Desert camping under the stars</li>
      <li>Date farm visits</li>
      <li>Historic Hejaz railway tour</li>
    </ul>
    <!-- Developer note: remove before going live! Part 1/3 of the flag: ${p1} -->
    <button onclick="bookNow()">Book Now</button>
  </main>
  <script src="script.js"></script>
</body>
</html>
HTML

cat > "$root/style.css" <<CSS
body {
  font-family: Arial, sans-serif;
  background-color: #f4e4c1;
  color: #4a3b2a;
  margin: 0;
  padding: 0;
}

header {
  background-color: #c2a36b;
  padding: 20px;
  text-align: center;
}

/* Part 2/3 of the flag: ${p2} */

main {
  padding: 20px;
}

button {
  background-color: #8b5e3c;
  color: white;
  border: none;
  padding: 10px 20px;
  cursor: pointer;
}
CSS

cat > "$root/script.js" <<JS
function bookNow() {
  alert("Sorry, all tours are fully booked this week!");
}

// Part 3/3 of the flag: ${p3}
JS

exec nginx -g 'daemon off;'
