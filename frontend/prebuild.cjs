const fs = require('fs');
const path = require('path');

console.log('🔧 Ejecutando prebuild para Docker compatibility...');

// Función para procesar archivos recursivamente
function processDirectory(dir) {
  const files = fs.readdirSync(dir);
  
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isDirectory() && !file.startsWith('.') && file !== 'node_modules') {
      processDirectory(filePath);
    } else if (file.endsWith('.tsx') || file.endsWith('.ts')) {
      processFile(filePath);
    }
  });
}

// Función para procesar cada archivo
function processFile(filePath) {
  try {
    let content = fs.readFileSync(filePath, 'utf8');
    let originalContent = content;
    
    // Regla 1: Convertir importaciones relativas de /lib/ a @/lib/index.ts
    content = content.replace(/from ['"](\.\.\/)+lib['"]/g, "from '@/lib/index.ts'");
    
    // Regla 2: Convertir importaciones de @/lib a @/lib/index.ts
    content = content.replace(/from ['"]@\/lib['"]/g, "from '@/lib/index.ts'");

    // Regla 3: Convertir importaciones de @/lib/index (sin extensión) a @/lib/index.ts
    content = content.replace(/from ['"]@\/lib\/index['"]/g, "from '@/lib/index.ts'");

    // Regla 4: Convertir importaciones dinámicas también
    content = content.replace(/import\(['"]@\/lib['"]\)/g, "import('@/lib/index.ts')");
    content = content.replace(/import\(['"]@\/lib\/index['"]\)/g, "import('@/lib/index.ts')");
    
    if (content !== originalContent) {
      fs.writeFileSync(filePath, content, 'utf8');
      console.log(`✅ Procesado: ${filePath}`);
    }
  } catch (error) {
    console.warn(`⚠️ Error procesando ${filePath}:`, error.message);
  }
}

// Ejecutar el procesamiento
try {
  processDirectory('./src');
  console.log('✅ Prebuild completado exitosamente');
} catch (error) {
  console.error('❌ Error en prebuild:', error);
  process.exit(1);
} 