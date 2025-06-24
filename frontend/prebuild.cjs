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
    
    // Convertir importaciones relativas a absolutas explícitas
    content = content.replace(/from ['"](\.\.\/)+lib['"]/g, "from '@/lib/index'");
    content = content.replace(/from ['"](\.\.\/)+lib\/([^'"]+)['"]/g, "from '@/lib/$2'");
    
    // Convertir importaciones de @/lib a @/lib/index
    content = content.replace(/from ['"]@\/lib['"]/g, "from '@/lib/index'");

    // Convertir importaciones dinámicas también
    content = content.replace(/import\(['"](\.\.\/)+lib['"]\)/g, "import('@/lib/index')");
    content = content.replace(/import\(['"]@\/lib['"]\)/g, "import('@/lib/index')");

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