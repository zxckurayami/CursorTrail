import QtQuick 2.15
import QtQuick.Window 2.15

Item {
    id: root
    width: Screen.width
    height: Screen.height
    property int maxPoints: 60
    property var points: []
    property real baseSize: 12
    property color trailColor: "#ff5555"
    property real trailAlpha: 1.0
    property var gradientColors: ["#ff5555"]
    property bool fadeEnabled: true
    property bool rgbEnabled: false
    property real rgbPhase: 0.0
    property bool glowEnabled: false
    property color glowColor: "#ffffff"
    property bool outlineEnabled: false
    property color outlineColor: "#000000"
    property bool sakuraEnabled: false
    property bool pixelEnabled: false
    property int petalMaxCount: 12
    property real petalSizeMul: 0.6

    Canvas {
        id: canvas
        anchors.fill: parent
        visible: true
        focus: false
        renderTarget: Canvas.FramebufferObject

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.clearRect(0, 0, width, height)
            ctx.globalCompositeOperation = 'source-over'
            // Сначала рисуем лепестки (если есть)
            if (sakuraEnabled && typeof(petals) !== 'undefined') {
                for (var pi = 0; pi < petals.length; ++pi) {
                    var pet = petals[pi]
                    ctx.beginPath()
                    ctx.globalAlpha = Math.max(0, pet.life/ pet.maxLife)
                    ctx.fillStyle = pet.color
                    // уменьшенная визуализация лепестка как эллипс
                    ctx.save()
                    ctx.translate(pet.x, pet.y)
                    ctx.rotate(pet.angle)
                    ctx.scale(1, 0.6)
                    ctx.arc(0, 0, pet.size * petalSizeMul, 0, Math.PI * 2)
                    ctx.restore()
                    ctx.fill()
                }
            }

            var len = points.length
            if (len >= 2) {
                // Catmull-Rom smoothing to produce a smoother path
                function catmullPoint(p0, p1, p2, p3, t) {
                    var t2 = t * t
                    var t3 = t2 * t
                    var x = 0.5 * ((2 * p1.x) + (-p0.x + p2.x) * t + (2*p0.x - 5*p1.x + 4*p2.x - p3.x) * t2 + (-p0.x + 3*p1.x - 3*p2.x + p3.x) * t3)
                    var y = 0.5 * ((2 * p1.y) + (-p0.y + p2.y) * t + (2*p0.y - 5*p1.y + 4*p2.y - p3.y) * t2 + (-p0.y + 3*p1.y - 3*p2.y + p3.y) * t3)
                    return {x: x, y: y}
                }

                function buildSmoothed(src, samples) {
                    var out = []
                    var n = src.length
                    for (var i = 0; i < n - 1; ++i) {
                        var p0 = (i - 1) >= 0 ? src[i - 1] : src[i]
                        var p1 = src[i]
                        var p2 = src[i + 1]
                        var p3 = (i + 2) < n ? src[i + 2] : src[i + 1]
                        for (var s = 0; s < samples; ++s) {
                            var t = s / samples
                            out.push(catmullPoint(p0, p1, p2, p3, t))
                        }
                    }
                    out.push(src[src.length - 1])
                    return out
                }

                var smoothSamples = (typeof root.smoothSamples !== 'undefined') ? root.smoothSamples : 2
                var smoothPts = buildSmoothed(points, smoothSamples)

                // Precompute cumulative length for smooth gradient mapping
                var cum = [0]
                var totalLen = 0
                for (var i = 1; i < smoothPts.length; ++i) {
                    var d = distance(smoothPts[i-1], smoothPts[i])
                    totalLen += d
                    cum.push(totalLen)
                }
                if (totalLen <= 0) totalLen = 1

                // Draw glow (around smoothed path)
                if (glowEnabled) {
                    for (var g = 3; g >= 1; --g) {
                        for (var i = 0; i < smoothPts.length - 1; ++i) {
                            var p0 = smoothPts[i]
                            var p1 = smoothPts[i+1]
                            var segMid = (cum[i] + cum[i+1]) * 0.5
                            var tNorm = segMid / totalLen
                            var alpha = trailAlpha * (fadeEnabled ? (1.0 - tNorm) : 1.0) * 0.12 * (g / 3)
                            var size = baseSize * (2.0 + g * 0.5) * (1.0 - tNorm*0.8)
                            
                            ctx.beginPath()
                            ctx.moveTo(p0.x, p0.y)
                            ctx.lineTo(p1.x, p1.y)
                            ctx.lineJoin = 'round'
                            ctx.lineCap = 'round'
                            ctx.globalAlpha = alpha
                            ctx.strokeStyle = glowColor
                            ctx.lineWidth = size
                            ctx.stroke()
                        }
                    }
                }

                // Draw outline (single contour)
                if (outlineEnabled) {
                    for (var i = 0; i < smoothPts.length - 1; ++i) {
                        var p0 = smoothPts[i]
                        var p1 = smoothPts[i+1]
                        var segMid = (cum[i] + cum[i+1]) * 0.5
                        var tNorm = segMid / totalLen
                        var alpha = trailAlpha * (fadeEnabled ? (1.0 - tNorm) : 1.0)
                        var size = baseSize * 1.5 * (1.0 - tNorm*0.8)
                        
                        ctx.beginPath()
                        ctx.moveTo(p0.x, p0.y)
                        ctx.lineTo(p1.x, p1.y)
                        ctx.lineJoin = 'round'
                        ctx.lineCap = 'round'
                        ctx.globalAlpha = alpha
                        ctx.strokeStyle = outlineColor
                        ctx.lineWidth = size
                        ctx.stroke()
                    }
                }

                // Draw main line along smoothed points with smooth gradient
                ctx.lineCap = 'round'
                for (var i = 0; i < smoothPts.length - 1; ++i) {
                    var p0 = smoothPts[i]
                    var p1 = smoothPts[i+1]
                    var segMid = (cum[i] + cum[i+1]) * 0.5
                    var tNorm = segMid / totalLen
                    var alpha = trailAlpha * (fadeEnabled ? (1.0 - tNorm) : 1.0)
                    var size = baseSize * (1.0 - tNorm*0.8)

                    // Smooth color interpolation by normalized distance
                    var segColor = trailColor
                    if (rgbEnabled) {
                        var h = (rgbPhase + (1 - tNorm) * 0.25) % 1.0
                        var rgb = hsvToRgb(h, 1.0, 1.0)
                        segColor = 'rgba(' + rgb.r + ',' + rgb.g + ',' + rgb.b + ',1)'
                    } else if (gradientColors.length > 0) {
                        segColor = interpolateGradient(gradientColors, tNorm)
                    }

                    if (pixelEnabled) {
                        var steps = Math.max(1, Math.floor(distance(p0, p1) / (size * 0.8)))
                        for (var s = 0; s <= steps; ++s) {
                            var u = s / steps
                            var x = p0.x + (p1.x - p0.x) * u
                            var y = p0.y + (p1.y - p0.y) * u
                            var sz = Math.max(1, Math.round(size * 0.9))
                            
                            // Draw glow for pixel
                            if (glowEnabled) {
                                for (var g = 3; g >= 1; --g) {
                                    ctx.beginPath()
                                    ctx.globalAlpha = alpha * 0.12 * (g / 3)
                                    ctx.fillStyle = glowColor
                                    var glowSize = Math.max(1, Math.round(size * (2.0 + g * 0.5) * 0.9))
                                    ctx.fillRect(
                                        Math.round(x - glowSize/2),
                                        Math.round(y - glowSize/2),
                                        glowSize,
                                        glowSize
                                    )
                                }
                            }
                            
                            // Draw outline for pixel
                            if (outlineEnabled) {
                                ctx.beginPath()
                                ctx.globalAlpha = alpha
                                ctx.fillStyle = outlineColor
                                var outlineSize = Math.max(1, Math.round(size * 1.5 * 0.9))
                                ctx.fillRect(
                                    Math.round(x - outlineSize/2),
                                    Math.round(y - outlineSize/2),
                                    outlineSize,
                                    outlineSize
                                )
                            }
                            
                            // Draw main pixel
                            ctx.beginPath()
                            ctx.globalAlpha = alpha
                            ctx.fillStyle = segColor
                            ctx.fillRect(
                                Math.round(x - sz/2),
                                Math.round(y - sz/2),
                                sz,
                                sz
                            )
                        }
                    } else {
                        ctx.beginPath()
                        ctx.globalAlpha = alpha
                        ctx.strokeStyle = segColor
                        ctx.lineWidth = size
                        ctx.moveTo(p0.x, p0.y)
                        ctx.lineTo(p1.x, p1.y)
                        ctx.stroke()
                    }
                }
            }
        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            enabled: false // disabled so it won't steal mouse events
        }
    }

    Timer {
        id: repaintTimer
        interval: 16
        repeat: true
        running: true
        onTriggered: canvas.requestPaint()
    }

    function pushPoint(x, y) {
        points.unshift({x: x, y: y})
        if (points.length > maxPoints) points.pop()
    }

    function setTrailColor(c) { trailColor = c }
    function clearPoints() { points = [] }
    function setMaxPoints(n) { maxPoints = n; if (points.length > maxPoints) points.length = maxPoints }
    function setBaseSize(s) { baseSize = s }
    function setAlpha(a) { trailAlpha = a }
    function setGradientColors(arr) { gradientColors = arr }
    function setFadeEnabled(v) { fadeEnabled = v }
    function setRgbEnabled(v) { rgbEnabled = v }
    function setRgbPhase(p) { rgbPhase = p }
    function setGlowEnabled(v) { glowEnabled = v }
    function setGlowColor(c) { glowColor = c }
    function setOutlineEnabled(v) { outlineEnabled = v }
    function setOutlineColor(c) { outlineColor = c }
    function setSakuraEnabled(v) { sakuraEnabled = v; if (!v) { petals = [] } }
    function setPixelEnabled(v) { pixelEnabled = v }

    // Вспомогательные функции
    function hexToRgb(hex) {
        var h = hex.replace('#','')
        if (h.length === 3) {
            h = h.split('').map(function(x){return x+x}).join('')
        }
        var r = parseInt(h.substr(0,2),16)
        var g = parseInt(h.substr(2,2),16)
        var b = parseInt(h.substr(4,2),16)
        return {r:r,g:g,b:b}
    }
    function interpolateGradient(arr, t) {
        if (arr.length === 1) return arr[0]
        var total = arr.length - 1
        var pos = t * total
        var idx = Math.floor(pos)
        if (idx >= total) idx = total - 1
        var local = pos - idx
        var c1 = hexToRgb(arr[idx])
        var c2 = hexToRgb(arr[idx+1])
        var r = Math.round(c1.r + (c2.r - c1.r) * local)
        var g = Math.round(c1.g + (c2.g - c1.g) * local)
        var b = Math.round(c1.b + (c2.b - c1.b) * local)
        return 'rgba(' + r + ',' + g + ',' + b + ',1)'
    }
    function hsvToRgb(h, s, v) {
        var r, g, b
        var i = Math.floor(h * 6)
        var f = h * 6 - i
        var p = v * (1 - s)
        var q = v * (1 - f * s)
        var t = v * (1 - (1 - f) * s)
        switch(i % 6) {
            case 0: r = v; g = t; b = p; break
            case 1: r = q; g = v; b = p; break
            case 2: r = p; g = v; b = t; break
            case 3: r = p; g = q; b = v; break
            case 4: r = t; g = p; b = v; break
            case 5: r = v; g = p; b = q; break
        }
        return {r: Math.round(r*255), g: Math.round(g*255), b: Math.round(b*255)}
    }

    function distance(a, b) {
        var dx = a.x - b.x
        var dy = a.y - b.y
        return Math.sqrt(dx*dx + dy*dy)
    }

    // Локальный таймер для RGB-фазы (если нужен)
    Timer {
        interval: 40
        repeat: true
        running: true
        onTriggered: {
            if (rgbEnabled) {
                rgbPhase = (rgbPhase + 0.005) % 1.0
            }
            // Обновление частиц
                if (sakuraEnabled) {
                    if (typeof(petals) === 'undefined') petals = []
                    for (var i = petals.length - 1; i >= 0; --i) {
                        var p = petals[i]
                        p.x += p.vx
                        p.y += p.vy
                        p.vy += 0.12 // gravity
                        p.angle += p.va
                        p.life -= 1
                        if (p.life <= 0) petals.splice(i,1)
                    }
                    canvas.requestPaint()
                }
        }
    }
    // Массив лепестков
    property var petals: []

    function spawnPetal(x, y, size, color) {
        if (typeof(petals) === 'undefined') petals = []
        // Limit total petals to avoid overload
        if (petals.length >= petalMaxCount) return
        var pet = { x: x + (Math.random()-0.5)*4, y: y + (Math.random()-0.5)*4, size: Math.max(1, size * 0.5), maxLife: 40 + Math.round(Math.random()*30), life: 40 + Math.round(Math.random()*30), vx: (Math.random()-0.5)*1.2, vy: - (0.5 + Math.random()*1.2), va: (Math.random()-0.5)*0.1, angle: Math.random()*6.28, color: color }
        petals.push(pet)
    }
}
