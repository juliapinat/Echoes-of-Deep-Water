const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

// --- CONFIGURAÇÕES DO MAPA MUNDIAL ---
const LARGURA_MUNDO = 2400;
const ALTURA_MUNDO = 1800;

// Paleta de Cores de acordo com o GDD
const PALETA = {
    abisso: "#040a14",
    parede: "#111827",
    bordaParede: "#1f2937",
    grade: "#0b1329",
    sonar: "#00ff8c",
    o2_estavel: "#00beff",
    o2_alerta: "#ef4444",
    monstro: "#dc2626",
    monstroOlho: "#f97316",
    plantaO2: "#10b981"
};

// --- VARIÁVEIS DE CONTROLE DE ESTADO ---
let teclas = {};
let partículas = [];
let sonares = [];
let barreiras = [];
let monstros = [];
let capsulasO2 = [];
let tremendoTela = 0;
let fimDeJogo = false;

// Captura de entradas do teclado
window.addEventListener("keydown", (e) => {
    teclas[e.key.toLowerCase()] = true;
    if (e.key === " " || e.code === "Space") {
        e.preventDefault();
        atirarSonar();
    }
});

window.addEventListener("keyup", (e) => {
    teclas[e.key.toLowerCase()] = false;
});

// --- CLASSES DAS ENTIDADES ---

class Mergulhador {
    constructor() {
        this.x = LARGURA_MUNDO / 2;
        this.y = ALTURA_MUNDO / 2;
        this.velocidade = 3.2;
        this.oxigenio = 100.0;
        this.angulo = 0;
        this.movendo = false;
        this.frameAnimacao = 0;
    }

    atualizar() {
        let dx = 0;
        let dy = 0;

        if (teclas['w'] || teclas['arrowup']) dy = -1;
        if (teclas['s'] || teclas['arrowdown']) dy = 1;
        if (teclas['a'] || teclas['arrowleft']) dx = -1;
        if (teclas['d'] || teclas['arrowright']) dx = 1;

        this.movendo = (dx !== 0 || dy !== 0);

        if (this.movendo) {
            if (dx !== 0 && dy !== 0) { // Correção de velocidade diagonal
                dx *= 0.7071;
                dy *= 0.7071;
            }

            this.angulo = Math.atan2(dy, dx);

            // Validação de colisão por eixos físicos
            let anteriorX = this.x;
            this.x += dx * this.velocidade;
            if (this.detectarColisaoObjeto()) this.x = anteriorX;

            let anteriorY = this.y;
            this.y += dy * this.velocidade;
            if (this.detectarColisaoObjeto()) this.y = anteriorY;

            this.oxigenio -= 0.05; // Gasto por nadar

            if (Math.random() < 0.12) {
                partículas.push(new Bolha(this.x, this.y, "rgba(180, 230, 255, 0.4)", 2));
            }
        } else {
            this.oxigenio -= 0.02; // Gasto passivo respirando
        }

        this.frameAnimacao = (this.frameAnimacao + 0.12) % 4;
    }

    detectarColisaoObjeto() {
        let caixaMergulhador = { x: this.x - 10, y: this.y - 10, w: 20, h: 20 };
        for (let b of barreiras) {
            if (caixaMergulhador.x < b.x + b.w && caixaMergulhador.x + caixaMergulhador.w > b.x &&
                caixaMergulhador.y < b.y + b.h && caixaMergulhador.y + caixaMergulhador.h > b.y) {
                return true;
            }
        }
        return false;
    }

    desenhar(camX, camY) {
        ctx.save();
        ctx.translate(this.x - camX, this.y - camY);
        ctx.rotate(this.angulo);

        let balanço = Math.sin(this.frameAnimacao) * 4;
        
        // Nadadeiras mecânicas animadas
        ctx.fillStyle = PALETA.bordaParede;
        ctx.fillRect(-13, -6 + (this.movendo ? balanço : 0), 5, 2);
        ctx.fillRect(-13, 4 - (this.movendo ? balanço : 0), 5, 2);

        // Cilindro traseiro de ar
        ctx.fillStyle = "#334155";
        ctx.fillRect(-7, -7, 5, 14);

        // Escafandro / Traje Principal
        ctx.fillStyle = "#1e293b";
        ctx.beginPath();
        ctx.arc(0, 0, 9, 0, Math.PI * 2);
        ctx.fill();

        // Visor iluminado azul
        ctx.fillStyle = PALETA.o2_estavel;
        ctx.beginPath();
        ctx.arc(5, 0, 3, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
    }
}

class Bolha {
    constructor(x, y, cor, raioMax) {
        this.x = x;
        this.y = y;
        this.cor = cor;
        this.vx = (Math.random() - 0.5) * 1.5;
        this.vy = (Math.random() - 0.5) * 1.5;
        this.vida = 1.0;
        this.raio = Math.random() * raioMax + 1;
    }
    atualizar() {
        this.x += this.vx;
        this.y += this.vy;
        this.vida -= 0.015;
    }
    desenhar(camX, camY) {
        if (this.vida <= 0) return;
        ctx.save();
        ctx.globalAlpha = this.vida;
        ctx.fillStyle = this.cor;
        ctx.beginPath();
        ctx.arc(this.x - camX, this.y - camY, this.raio, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
    }
}

class OndaSonar {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.raio = 0;
        this.raioMax = 420;
        this.ativo = true;
    }
    atualizar() {
        this.raio += 5.5;
        if (this.raio > this.raioMax) this.ativo = false;
    }
    desenhar(camX, camY) {
        if (!this.ativo) return;
        ctx.save();
        ctx.strokeStyle = PALETA.sonar;
        ctx.globalAlpha = 1 - (this.raio / this.raioMax);
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.arc(this.x - camX, this.y - camY, this.raio, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
    }
}

class CriaturaAbissal {
    constructor() {
        this.gerarPosicaoValida();
        this.estado = "PATRULHA";
        this.velocidade = 0.9;
        this.angulo = Math.random() * Math.PI * 2;
        this.tempoAlerta = 0;
        this.animFrame = Math.random() * 5;
    }

    gerarPosicaoValida() {
        this.x = Math.random() * (LARGURA_MUNDO - 300) + 150;
        this.y = Math.random() * (ALTURA_MUNDO - 300) + 150;
    }

    atualizar(jogador, sonar) {
        this.animFrame += 0.12;
        let distMergulhador = Math.hypot(jogador.x - this.x, jogador.y - this.y);

        // Inteligência Artificial do GDD: Escuta ondas mecânicas do Sonar
        if (sonar && sonar.ativo) {
            let distOnda = Math.hypot(sonar.x - this.x, sonar.y - this.y);
            if (Math.abs(distOnda - sonar.raio) < 40) {
                this.estado = "PERSEGUICAO";
                this.tempoAlerta = 200; // Tempo focado em caçar
            }
        }

        if (this.estado === "PERSEGUICAO") {
            this.angulo = Math.atan2(jogador.y - this.y, jogador.x - this.x);
            this.x += Math.cos(this.angulo) * (this.velocidade * 2.2);
            this.y += Math.sin(this.angulo) * (this.velocidade * 2.2);
            this.tempoAlerta--;
            if (this.tempoAlerta <= 0 && distMergulhador > 250) this.estado = "PATRULHA";
        } else {
            if (Math.random() < 0.015) this.angulo += (Math.random() - 0.5) * 2;
            this.x += Math.cos(this.angulo) * this.velocidade;
            this.y += Math.sin(this.angulo) * this.velocidade;
        }
    }

    desenhar(camX, camY, sonar) {
        let visivel = false;
        if (this.estado === "PERSEGUICAO") {
            visivel = true;
        } else if (sonar && sonar.active) {
            let d = Math.hypot(this.x - sonar.x, this.y - sonar.y);
            if (d < sonar.raio) visivel = true;
        }

        if (!visivel) return;

        ctx.save();
        ctx.translate(this.x - camX, this.y - camY);
        ctx.rotate(this.angulo);

        let tentaculo = Math.sin(this.animFrame) * 4;
        ctx.fillStyle = "#7f1d1d";
        ctx.fillRect(-20, -6 + tentaculo, 10, 2);
        ctx.fillRect(-20, 4 - tentaculo, 10, 2);

        // Núcleo Biológico Agressivo
        ctx.fillStyle = PALETA.monstro;
        ctx.beginPath();
        ctx.arc(0, 0, 9, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = PALETA.monstroOlho;
        ctx.beginPath();
        ctx.arc(3, 0, 3, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
    }
}

class AlgaOxigenio {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.disponivel = true;
        this.frequencia = Math.random() * 3;
    }
    desenhar(camX, camY) {
        if (!this.disponivel) return;
        this.frequencia += 0.05;
        let pulsação = Math.sin(this.frequencia) * 2.5;

        ctx.save();
        ctx.fillStyle = "#064e3b";
        ctx.beginPath();
        ctx.arc(this.x - camX, this.y - camY, 13, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = PALETA.plantaO2;
        ctx.beginPath();
        ctx.arc(this.x - camX, this.y - camY, 7 + pulsação, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
    }
}

// --- CONSTRUÇÃO DO CENÁRIO DO TRABALHO ---
function estruturarLabirintoCaverna() {
    // Paredes de Isolamento das bordas
    barreiras.push({ x: 0, y: 0, w: LARGURA_MUNDO, h: 40 });
    barreiras.push({ x: 0, y: ALTURA_MUNDO - 40, w: LARGURA_MUNDO, h: 40 });
    barreiras.push({ x: 0, y: 0, w: 40, h: ALTURA_MUNDO });
    barreiras.push({ x: LARGURA_MUNDO - 40, y: 0, w: 40, h: ALTURA_MUNDO });

    // Blocos rochosos internos estruturados
    for (let i = 0; i < 24; i++) {
        let largura = Math.floor(Math.random() * 180) + 140;
        let altura = Math.floor(Math.random() * 180) + 140;
        let x = Math.floor(Math.random() * (LARGURA_MUNDO - 400)) + 150;
        let y = Math.floor(Math.random() * (ALTURA_MUNDO - 400)) + 150;

        // Zona segura no meio para o jogador iniciar vivo
        let zonaInviolavel = { x: LARGURA_MUNDO / 2 - 180, y: ALTURA_MUNDO / 2 - 180, w: 360, h: 360 };
        if (!(x < zonaInviolavel.x + zonaInviolavel.w && x + largura > zonaInviolavel.x && 
              y < zonaInviolavel.y + zonaInviolavel.h && y + altura > zonaInviolavel.y)) {
            barreiras.push({ x, y, w: largura, h: altura });
        }
    }

    // Geração de recursos vitais
    for (let i = 0; i < 10; i++) {
        let rx = Math.random() * (LARGURA_MUNDO - 300) + 150;
        let ry = Math.random() * (ALTURA_MUNDO - 300) + 150;
        capsulasO2.push(new AlgaOxigenio(rx, ry));
    }

    // Inserção dos predadores da fauna cega
    for (let i = 0; i < 10; i++) {
    }
}