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
    let modified = false;
    
    // Reemplazar importaciones problemáticas con paths absolutos
    const replacements = [
      // Importaciones estáticas
      { from: /from ['"]\.\.\/lib['"];?/g, to: "from '@/lib';" },
      { from: /from ['"]\.\.\/\.\.\/lib['"];?/g, to: "from '@/lib';" },
      { from: /from ['"]\.\.\/lib\/([^'"]+)['"];?/g, to: "from '@/lib/$1';" },
      { from: /from ['"]\.\.\/\.\.\/lib\/([^'"]+)['"];?/g, to: "from '@/lib/$1';" },
      
      // Importaciones dinámicas (await import)
      { from: /await import\(['"]\.\.\/lib['"]\)/g, to: "await import('@/lib')" },
      { from: /await import\(['"]\.\.\/\.\.\/lib['"]\)/g, to: "await import('@/lib')" },
      { from: /await import\(['"]\.\.\/lib\/([^'"]+)['"]\)/g, to: "await import('@/lib/$1')" },
      { from: /await import\(['"]\.\.\/\.\.\/lib\/([^'"]+)['"]\)/g, to: "await import('@/lib/$1')" },
      
      // Importaciones dinámicas (import())
      { from: /import\(['"]\.\.\/lib['"]\)/g, to: "import('@/lib')" },
      { from: /import\(['"]\.\.\/\.\.\/lib['"]\)/g, to: "import('@/lib')" },
      { from: /import\(['"]\.\.\/lib\/([^'"]+)['"]\)/g, to: "import('@/lib/$1')" },
      { from: /import\(['"]\.\.\/\.\.\/lib\/([^'"]+)['"]\)/g, to: "import('@/lib/$1')" },
    ];
    
    replacements.forEach(({ from, to }) => {
      if (from.test(content)) {
        content = content.replace(from, to);
        modified = true;
      }
    });
    
    if (modified) {
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