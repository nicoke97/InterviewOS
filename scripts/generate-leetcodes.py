#!/usr/bin/env python3
"""Generate LeetCodes interview practice catalog (Blind 75 core MVP)."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "content" / "leetcodes"
SCHEDULE = ROOT / "content" / "schedule" / "leetcode-interview.yaml"

TOPIC_GUIDES = {
    "arrays_hashing": {
        "approach": "Muchos problemas de arrays se resuelven recorriendo una vez y usando un hash map o set para lookup O(1). Pregúntate: ¿qué necesito recordar de lo que ya vi?",
        "learning": [
            "Hash maps y sets para búsquedas y conteos en O(1)",
            "Trade-off espacio extra vs tiempo de ejecución",
            "Cuándo ordenar primero vs usar estructura auxiliar",
        ],
        "interview_questions": [
            "¿Cuál es la complejidad temporal y espacial?",
            "¿Qué pasa si el array está ordenado — cambiaría tu enfoque?",
            "¿Cómo manejarías duplicados o restricciones de memoria?",
        ],
    },
    "two_pointers": {
        "approach": "Con dos punteros (o uno a cada extremo) puedes reducir búsquedas O(n²) a O(n). Funciona bien en arrays ordenados o cuando buscas pares/tripletas con condiciones monótonas.",
        "learning": [
            "Puntero izquierdo/derecho en arrays ordenados",
            "Cuándo mover cada puntero según la suma o comparación",
            "Evitar tripletas duplicadas con sort + skip",
        ],
        "interview_questions": [
            "¿Por qué two pointers y no hash map aquí?",
            "¿Qué casos borde hay (array vacío, sin solución)?",
            "¿Cuál es la complejidad y se puede mejorar?",
        ],
    },
    "sliding_window": {
        "approach": "Mantén una ventana [left, right] que cumple una condición y expande/contrae según crece o viola la regla. Ideal para substrings/subarrays contiguos.",
        "learning": [
            "Ventana fija vs ventana variable",
            "Actualizar contadores al entrar/salir de la ventana",
            "Cuándo mover left vs right",
        ],
        "interview_questions": [
            "¿Cómo garantizas que no revisas de más cada posición?",
            "¿Qué estructura auxiliar necesitas (set, dict de frecuencias)?",
            "Complejidad temporal y espacial de tu solución",
        ],
    },
    "stack": {
        "approach": "Un stack (LIFO) resuelve problemas de emparejamiento, anidamiento o 'último relevante'. Piensa en qué debes deshacer al encontrar un cierre o un valor menor.",
        "learning": [
            "Stack para paréntesis y expresiones",
            "Monotonic stack para mínimos/máximos en ventana",
            "Simular operaciones con dos stacks si hace falta",
        ],
        "interview_questions": [
            "¿Por qué stack y no otro enfoque?",
            "¿Qué pasa con input vacío o un solo elemento?",
            "¿Se puede hacer en O(1) por operación?",
        ],
    },
    "binary_search": {
        "approach": "Si el espacio de búsqueda es monótono (sorted array o respuesta sí/no), usa binary search. Define bien lo que buscas: índice, valor o condición mínima que cumple.",
        "learning": [
            "Invariante: la respuesta está en [lo, hi]",
            "Diferencia entre buscar valor exacto vs primera posición válida",
            "Binary search en espacio de respuestas (no solo arrays)",
        ],
        "interview_questions": [
            "¿Por qué O(log n) y cuándo no aplica?",
            "¿Cómo evitas off-by-one en los límites?",
            "¿Qué haces si el array está rotado?",
        ],
    },
    "linked_list": {
        "approach": "En listas enlazadas usa punteros lentos/rápidos (Floyd), prev para invertir, o dummy head para simplificar bordes. Dibuja los punteros antes de codear.",
        "learning": [
            "Dummy node para evitar casos especiales en head",
            "Fast/slow pointers para ciclos y mitad",
            "Invertir y fusionar reconectando next",
        ],
        "interview_questions": [
            "¿Complejidad temporal y espacial?",
            "¿Cómo detectarías un ciclo sin set extra?",
            "¿Iterativo vs recursivo — trade-offs?",
        ],
    },
    "trees": {
        "approach": "Recorridos DFS (pre/in/post) o BFS por niveles. Define el caso base (None), qué retornas en cada nodo y cómo combinas hijos izquierdo/derecho.",
        "learning": [
            "DFS recursivo vs iterativo con stack",
            "BFS con cola para niveles",
            "Propagar min/max en BST validation",
        ],
        "interview_questions": [
            "¿Recursivo o iterativo — cuándo cada uno?",
            "¿Complejidad en árbol balanceado vs degenerado?",
            "¿Cómo serializar/deserializar el árbol?",
        ],
    },
    "dp_1d": {
        "approach": "Define dp[i] = mejor respuesta hasta la posición i (o para amount i). La transición suele mirar 1–2 estados anteriores. Optimiza espacio si solo necesitas los últimos valores.",
        "learning": [
            "Formular estado y transición antes de codear",
            "Bottom-up vs top-down con memo",
            "Rolling array para O(1) espacio extra",
        ],
        "interview_questions": [
            "¿Cuál es tu estado y por qué?",
            "¿Se puede reducir espacio a O(1)?",
            "¿Cómo detectarías solapamiento de subproblemas?",
        ],
    },
    "graphs": {
        "approach": "Modela nodos y aristas; elige BFS (mínimos pasos/capa), DFS (componentes, ciclos) o topological sort (dependencias). Marca visitados para no repetir.",
        "learning": [
            "BFS vs DFS — cuándo cada uno",
            "Detección de ciclos y orden topológico",
            "Grid como grafo implícito (4/8 direcciones)",
        ],
        "interview_questions": [
            "¿Representación: lista de adyacencia vs matriz?",
            "¿Cómo detectas un ciclo?",
            "Complejidad en V vértices y E aristas",
        ],
    },
    "intervals": {
        "approach": "Ordena por inicio (o fin). Fusiona o inserta comparando solapamientos: intervalos se solapan si start <= prev_end.",
        "learning": [
            "Sort como primer paso casi siempre",
            "Merge lineal después de ordenar",
            "Insert con binary search en casos avanzados",
        ],
        "interview_questions": [
            "¿Por qué ordenar primero?",
            "¿Cómo manejas intervalos abiertos/cerrados?",
            "Complejidad total de tu algoritmo",
        ],
    },
}

PROBLEM_HINTS = {
    "lc-two-sum": [
        "Para cada número nums[i], el complemento es target - nums[i].",
        "Guarda en un dict {valor: índice} mientras recorres; antes de guardar, revisa si el complemento ya está.",
        "Un solo pass: O(n) tiempo, O(n) espacio.",
    ],
    "lc-contains-duplicate": [
        "¿Necesitas contar o solo saber si hay repetido?",
        "Un set de valores vistos: si nums[i] ya está, return True.",
        "Alternativa: ordenar y comparar vecinos — O(n log n) sin espacio extra.",
    ],
    "lc-valid-anagram": [
        "Misma longitud y mismas frecuencias de letras.",
        "Cuenta chars de s en un dict y resta con t; o usa Counter(s) == Counter(t).",
        "Si len(s) != len(t), return False de inmediato.",
    ],
    "lc-best-time-stock": [
        "Quieres max(prices[j] - prices[i]) con j > i.",
        "Recorre precios llevando min_price visto; actualiza max_profit con price - min_price.",
        "Un pass O(n), O(1) espacio.",
    ],
    "lc-group-anagrams": [
        "Anagramas comparten la misma 'firma': letras ordenadas o tupla de conteos.",
        "dict[firma] -> lista de strings; agrupa strs por firma.",
        "Firma con tuple(sorted(s)) es simple y suficiente aquí.",
    ],
    "lc-top-k-frequent": [
        "Primero cuenta frecuencias con Counter o dict.",
        "Luego extrae los k más frecuentes: bucket sort por freq o heap de tamaño k.",
        "Bucket: lista indexada por frecuencia — O(n) promedio.",
    ],
    "lc-valid-palindrome": [
        "Normaliza: solo alfanuméricos en minúsculas (two pointers o filtrar).",
        "Compara chars en left y right moviendo hacia el centro.",
        "Salta chars no alfanuméricos antes de comparar.",
    ],
    "lc-two-sum-ii": [
        "Array ordenado: punteros left=0, right=len-1.",
        "Si suma < target, left++; si suma > target, right--.",
        "Retorna índices 1-based: [left+1, right+1].",
    ],
    "lc-3sum": [
        "Ordena nums; fija i y busca par con two sum en i+1..n-1.",
        "Si nums[i] == nums[i-1], salta duplicados en i.",
        "Igual al mover left/right cuando encuentras tripletas.",
    ],
    "lc-container-water": [
        "Two pointers en los extremos del array height.",
        "Área = min(h[left], h[right]) * (right - left).",
        "Mueve el puntero del lado más bajo — el otro no puede mejorar el área.",
    ],
    "lc-longest-substring": [
        "Ventana [left, right] con set o dict de última posición de cada char.",
        "Expande right; si char repetido, mueve left después de la última ocurrencia.",
        "Guarda max(right - left + 1) en cada paso.",
    ],
    "lc-min-window-substring": [
        "Ventana variable con contadores de chars de t en s.",
        "Expande right hasta cubrir t; luego contrae left minimizando ventana.",
        "Lleva formed/required para saber cuándo la ventana es válida.",
    ],
    "lc-valid-parentheses": [
        "Stack de aperturas; al ver cierre, debe matchear top.",
        "Mapa {')':'(', '}':'{', ']':'['}.",
        "Al final stack debe estar vacío.",
    ],
    "lc-min-stack": [
        "Dos stacks: valores y mínimos actuales en paralelo.",
        "En push: apila valor y min(val, top_mins o val).",
        "getMin en O(1) leyendo top de mins.",
    ],
    "lc-binary-search": [
        "Clásico: lo, hi, mid = (lo+hi)//2.",
        "Si nums[mid] < target, lo = mid+1; si >, hi = mid-1.",
        "Retorna -1 si lo > hi.",
    ],
    "lc-search-rotated": [
        "Binary search: una mitad siempre está ordenada.",
        "Comprueba si target está en la mitad ordenada; si no, busca en la otra.",
        "Identifica mitad ordenada comparando nums[mid] con nums[lo].",
    ],
    "lc-reverse-linked-list": [
        "Tres punteros: prev, curr, next mientras recorres.",
        "curr.next = prev; avanza los tres.",
        "Retorna prev al final (nueva head).",
    ],
    "lc-merge-two-lists": [
        "Dummy head + puntero tail; compara heads de a y b.",
        "Enlaza el menor y avanza ese puntero.",
        "Al terminar, enlaza el resto no vacío.",
    ],
    "lc-linked-list-cycle": [
        "Floyd: slow avanza 1, fast avanza 2; ciclo si se encuentran.",
        "En este MVP, pos >= 0 indica ciclo en la representación dada.",
        "En entrevista real: detectar ciclo sin modificar la lista.",
    ],
    "lc-max-depth-tree": [
        "DFS: 1 + max(depth izq, depth der); None -> 0.",
        "BFS: cuenta niveles con cola.",
        "Caso base: nodo None retorna 0.",
    ],
    "lc-invert-tree": [
        "Swap hijos izquierdo y derecho en cada nodo (DFS o BFS).",
        "Recursivo: invert(left), invert(right), swap.",
        "Retorna la raíz (misma referencia).",
    ],
    "lc-validate-bst": [
        "Pasa rango (min, max) válido por nodo.",
        "Nodo debe estar en (min, max); valida subárboles con rangos actualizados.",
        "None siempre es válido.",
    ],
    "lc-climbing-stairs": [
        "dp[i] = formas de llegar al escalón i.",
        "dp[i] = dp[i-1] + dp[i-2] — igual que Fibonacci.",
        "Optimiza a dos variables: prev1, prev2.",
    ],
    "lc-house-robber": [
        "dp[i] = max dinero robando hasta casa i.",
        "dp[i] = max(dp[i-1], dp[i-2] + nums[i]) — no robas adyacentes.",
        "Solo necesitas dos valores anteriores.",
    ],
    "lc-coin-change": [
        "dp[a] = mínimo monedas para amount a; inicializa inf excepto dp[0]=0.",
        "Para cada coin y cada amount, dp[a] = min(dp[a], dp[a-coin]+1).",
        "Retorna dp[amount] si no es inf, else -1.",
    ],
    "lc-number-islands": [
        "Por cada '1' no visitado, DFS/BFS marca toda la isla como visitada.",
        "Incrementa contador por cada componente nueva.",
        "Marca visitados in-place o con set de (r,c).",
    ],
    "lc-course-schedule": [
        "Grafo de prerequisitos; ciclo => no se puede terminar.",
        "Topological sort (Kahn BFS o DFS con estados visiting/visited).",
        "n nodos, aristas prerequisites[i] = [a, b] significa b -> a.",
    ],
    "lc-merge-intervals": [
        "Ordena por start; fusiona si intervals[i].start <= merged[-1].end.",
        "Si solapan, extiende end del último intervalo.",
        "Si no, append nuevo intervalo.",
    ],
}


DESCRIPTIONS_ES: dict[str, str] = {
    "lc-two-sum": (
        "Dado un arreglo de enteros nums y un entero target, devuelve los índices de "
        "los dos números tales que sumen target.\n\n"
        "Puedes asumir que cada entrada tiene exactamente una solución y no puedes usar "
        "el mismo elemento dos veces. Puedes devolver la respuesta en cualquier orden."
    ),
    "lc-contains-duplicate": (
        "Dado un arreglo de enteros nums, devuelve true si algún valor aparece al "
        "menos dos veces y false si todos los elementos son distintos."
    ),
    "lc-valid-anagram": (
        "Dadas dos cadenas s y t, devuelve true si t es un anagrama de s y false en "
        "caso contrario.\n\n"
        "Un anagrama es una palabra formada reordenando las letras de otra, usando "
        "todas las letras originales exactamente una vez."
    ),
    "lc-best-time-stock": (
        "Se te da un arreglo prices donde prices[i] es el precio de una acción en el "
        "día i.\n\n"
        "Quieres maximizar tu beneficio eligiendo un día para comprar y otro "
        "posterior para vender. Devuelve el beneficio máximo posible. Si no puedes "
        "obtener beneficio, devuelve 0."
    ),
    "lc-group-anagrams": (
        "Dado un arreglo de cadenas strs, agrupa los anagramas entre sí. "
        "Puedes devolver la respuesta en cualquier orden y el orden dentro de cada "
        "grupo tampoco importa."
    ),
    "lc-top-k-frequent": (
        "Dado un arreglo de enteros nums y un entero k, devuelve los k elementos "
        "más frecuentes. Puedes devolver la respuesta en cualquier orden."
    ),
    "lc-valid-palindrome": (
        "Dada una cadena s, devuelve true si es un palíndromo al considerar solo "
        "caracteres alfanuméricos e ignorando mayúsculas/minúsculas.\n\n"
        "Un palíndromo se lee igual de izquierda a derecha que de derecha a izquierda."
    ),
    "lc-two-sum-ii": (
        "Dado un arreglo de enteros numbers ordenado en orden no decreciente y un "
        "entero target, devuelve los índices (basados en 1) de los dos números que "
        "sumen target.\n\n"
        "Puedes asumir que cada entrada tiene exactamente una solución y no puedes "
        "usar el mismo elemento dos veces. Debes resolverlo con complejidad O(n) "
        "usando solo memoria extra constante."
    ),
    "lc-3sum": (
        "Dado un arreglo de enteros nums, devuelve todas las tripletas únicas "
        "[nums[i], nums[j], nums[k]] tales que i != j, i != k, j != k y "
        "nums[i] + nums[j] + nums[k] == 0.\n\n"
        "La lista de salida no debe contener tripletas duplicadas."
    ),
    "lc-container-water": (
        "Se te da n líneas verticales no negativas en un plano cartesiano, donde la "
        "i-ésima línea va de (i, 0) a (i, height[i]).\n\n"
        "Encuentra dos líneas que, junto con el eje x, formen un contenedor que "
        "almacene la mayor cantidad de agua posible. Devuelve esa cantidad máxima."
    ),
    "lc-longest-substring": (
        "Dada una cadena s, encuentra la longitud de la subcadena más larga sin "
        "caracteres repetidos."
    ),
    "lc-min-window-substring": (
        "Dadas dos cadenas s y t, devuelve la subcadena mínima de s que contenga "
        "todos los caracteres de t (incluidos duplicados). Si no existe, devuelve "
        "una cadena vacía."
    ),
    "lc-valid-parentheses": (
        "Dada una cadena s que contiene solo los caracteres '(', ')', '{', '}', "
        "'[' y ']', determina si la cadena es válida.\n\n"
        "Una cadena es válida si: cada paréntesis de apertura se cierra con el "
        "mismo tipo; los paréntesis se cierran en el orden correcto; y cada cierre "
        "tiene su correspondiente apertura."
    ),
    "lc-min-stack": (
        "Diseña una pila que soporte push, pop, top y recuperar el elemento mínimo "
        "en O(1).\n\n"
        "En este ejercicio recibes una lista ops con operaciones en orden: "
        "['push', val], ['pop'], ['top'] o ['getMin']. Devuelve una lista con el "
        "resultado de cada top y getMin (None para las demás operaciones)."
    ),
    "lc-binary-search": (
        "Dado un arreglo nums ordenado en orden ascendente (sin duplicados) y un "
        "entero target, devuelve el índice de target si está en nums, o -1 si no "
        "está.\n\n"
        "Debes resolverlo con complejidad O(log n)."
    ),
    "lc-search-rotated": (
        "Dado un arreglo nums ordenado en orden ascendente que fue rotado entre 1 y "
        "n posiciones, y un entero target, devuelve el índice de target si está en "
        "nums, o -1 si no está.\n\n"
        "Debes resolverlo con complejidad O(log n)."
    ),
    "lc-reverse-linked-list": (
        "Dada una lista enlazada representada como un arreglo de valores en orden, "
        "inviértela y devuelve los valores en el nuevo orden.\n\n"
        "Por ejemplo, [1, 2, 3, 4, 5] se convierte en [5, 4, 3, 2, 1]."
    ),
    "lc-merge-two-lists": (
        "Dadas dos listas enlazadas ordenadas representadas como arreglos a y b, "
        "fusionalas en una sola lista ordenada y devuelve sus valores.\n\n"
        "El resultado debe formarse concatenando los nodos de a y b en orden "
        "creciente."
    ),
    "lc-linked-list-cycle": (
        "Se te da una lista enlazada representada por values (valores en orden) y "
        "pos (índice donde el último nodo apunta hacia atrás, o -1 si no hay ciclo).\n\n"
        "Devuelve true si la lista tiene un ciclo y false en caso contrario."
    ),
    "lc-max-depth-tree": (
        "Dado un árbol binario en representación por niveles (arreglo donde None "
        "significa nodo vacío), devuelve su profundidad máxima.\n\n"
        "La profundidad es el número de nodos a lo largo del camino más largo desde "
        "la raíz hasta un nodo hoja."
    ),
    "lc-invert-tree": (
        "Dado un árbol binario en representación por niveles (arreglo con None para "
        "nodos vacíos), invierte el árbol (intercambia hijo izquierdo y derecho en "
        "cada nodo) y devuelve la nueva representación por niveles."
    ),
    "lc-validate-bst": (
        "Dado un árbol binario en representación por niveles, determina si es un "
        "árbol binario de búsqueda (BST) válido.\n\n"
        "Un BST válido cumple que el subárbol izquierdo de cada nodo contiene solo "
        "valores menores y el subárbol derecho solo valores mayores."
    ),
    "lc-climbing-stairs": (
        "Estás subiendo una escalera. Cada vez puedes subir 1 o 2 escalones.\n\n"
        "Dado n (número de escalones), devuelve cuántas formas distintas hay de "
        "llegar a la cima."
    ),
    "lc-house-robber": (
        "Eres un ladrón planeando robar casas en una calle. Cada casa tiene cierta "
        "cantidad de dinero. No puedes robar dos casas adyacentes porque activarían "
        "la alarma.\n\n"
        "Dado nums donde nums[i] es el dinero en la casa i, devuelve la cantidad "
        "máxima que puedes robar sin alertar a la policía."
    ),
    "lc-coin-change": (
        "Dado un arreglo coins de distintas denominaciones y un entero amount, "
        "devuelve la cantidad mínima de monedas necesarias para formar amount. "
        "Si no es posible, devuelve -1.\n\n"
        "Puedes usar cada denominación tantas veces como quieras."
    ),
    "lc-number-islands": (
        "Dado un grid m x n de caracteres '1' (tierra) y '0' (agua), devuelve el "
        "número de islas.\n\n"
        "Una isla está rodeada de agua y se forma conectando tierras adyacentes "
        "horizontal o verticalmente."
    ),
    "lc-course-schedule": (
        "Hay numCourses cursos numerados de 0 a numCourses - 1. Recibes "
        "prerequisites donde [a, b] indica que debes tomar el curso b antes del "
        "curso a.\n\n"
        "Devuelve true si puedes terminar todos los cursos y false si existe un "
        "ciclo de prerequisitos imposible de resolver."
    ),
    "lc-merge-intervals": (
        "Dado un arreglo de intervalos donde intervals[i] = [start, end], fusiona "
        "todos los intervalos solapados y devuelve un arreglo con los intervalos "
        "resultantes.\n\n"
        "Dos intervalos se solapan si el inicio de uno es menor o igual al final "
        "del otro."
    ),
}

DESCRIPTIONS_EN: dict[str, str] = {
    "lc-two-sum": (
        "Given an array of integers nums and an integer target, return the indices "
        "of the two numbers such that they add up to target.\n\n"
        "You may assume that each input has exactly one solution, and you may not "
        "use the same element twice. You can return the answer in any order."
    ),
    "lc-contains-duplicate": (
        "Given an integer array nums, return true if any value appears at least "
        "twice in the array, and false if every element is distinct."
    ),
    "lc-valid-anagram": (
        "Given two strings s and t, return true if t is an anagram of s, and false "
        "otherwise.\n\n"
        "An anagram is a word formed by rearranging the letters of another, using "
        "all the original letters exactly once."
    ),
    "lc-best-time-stock": (
        "You are given an array prices where prices[i] is the price of a stock on "
        "day i.\n\n"
        "You want to maximize profit by choosing one day to buy and a different "
        "day in the future to sell. Return the maximum profit you can achieve. If "
        "you cannot make a profit, return 0."
    ),
    "lc-group-anagrams": (
        "Given an array of strings strs, group the anagrams together. You can "
        "return the answer in any order, and the order within each group does not "
        "matter."
    ),
    "lc-top-k-frequent": (
        "Given an integer array nums and an integer k, return the k most frequent "
        "elements. You may return the answer in any order."
    ),
    "lc-valid-palindrome": (
        "Given a string s, return true if it is a palindrome considering only "
        "alphanumeric characters and ignoring cases.\n\n"
        "A palindrome reads the same forward and backward."
    ),
    "lc-two-sum-ii": (
        "Given a 1-indexed array of integers numbers that is sorted in non-decreasing "
        "order, find two numbers such that they add up to a specific target number.\n\n"
        "Return the indices (1-indexed) of the two numbers. You may assume each "
        "input has exactly one solution, and you may not use the same element twice. "
        "Your solution must use only constant extra memory and run in O(n) time."
    ),
    "lc-3sum": (
        "Given an integer array nums, return all unique triplets [nums[i], nums[j], "
        "nums[k]] such that i != j, i != k, j != k, and nums[i] + nums[j] + "
        "nums[k] == 0.\n\n"
        "The output must not contain duplicate triplets."
    ),
    "lc-container-water": (
        "You are given n non-negative integers height where the ith line goes from "
        "(i, 0) to (i, height[i]).\n\n"
        "Find two lines that together with the x-axis form a container that holds "
        "as much water as possible. Return the maximum amount of water the "
        "container can store."
    ),
    "lc-longest-substring": (
        "Given a string s, find the length of the longest substring without "
        "repeating characters."
    ),
    "lc-min-window-substring": (
        "Given two strings s and t, return the minimum window substring of s such "
        "that every character in t (including duplicates) is included in the "
        "window. If there is no such substring, return an empty string."
    ),
    "lc-valid-parentheses": (
        "Given a string s containing just the characters '(', ')', '{', '}', '[' "
        "and ']', determine if the input string is valid.\n\n"
        "A string is valid if open brackets are closed by the same type of "
        "brackets, in the correct order, and each close bracket has a matching "
        "open bracket of the same type."
    ),
    "lc-min-stack": (
        "Design a stack that supports push, pop, top, and retrieving the minimum "
        "element in constant time.\n\n"
        "In this exercise you receive a list ops of operations in order: "
        "['push', val], ['pop'], ['top'], or ['getMin']. Return a list with the "
        "result of each top and getMin (None for other operations)."
    ),
    "lc-binary-search": (
        "Given an array of integers nums which is sorted in ascending order, and an "
        "integer target, return the index of target if it is in nums, or -1 if it "
        "is not.\n\n"
        "You must write an algorithm with O(log n) runtime complexity."
    ),
    "lc-search-rotated": (
        "Given an integer array nums sorted in ascending order that has been "
        "rotated between 1 and n times, and an integer target, return the index of "
        "target if it is in nums, or -1 if it is not.\n\n"
        "You must write an algorithm with O(log n) runtime complexity."
    ),
    "lc-reverse-linked-list": (
        "Given a linked list represented as an array of values in order, reverse it "
        "and return the values in the new order.\n\n"
        "For example, [1, 2, 3, 4, 5] becomes [5, 4, 3, 2, 1]."
    ),
    "lc-merge-two-lists": (
        "Given two sorted linked lists represented as arrays a and b, merge them "
        "into one sorted list and return its values.\n\n"
        "The result should be formed by splicing together the nodes of a and b in "
        "ascending order."
    ),
    "lc-linked-list-cycle": (
        "You are given a linked list represented by values (node values in order) "
        "and pos (the index the tail connects to for a cycle, or -1 if there is "
        "no cycle).\n\n"
        "Return true if there is a cycle in the linked list, and false otherwise."
    ),
    "lc-max-depth-tree": (
        "Given a binary tree in level-order representation (an array where None "
        "means an empty node), return its maximum depth.\n\n"
        "The maximum depth is the number of nodes along the longest path from the "
        "root down to the farthest leaf node."
    ),
    "lc-invert-tree": (
        "Given a binary tree in level-order representation (array with None for "
        "empty nodes), invert the tree (swap left and right children at every "
        "node) and return the new level-order representation."
    ),
    "lc-validate-bst": (
        "Given a binary tree in level-order representation, determine if it is a "
        "valid binary search tree (BST).\n\n"
        "A valid BST has every node's left subtree containing only values less than "
        "the node, and every right subtree containing only values greater than the "
        "node."
    ),
    "lc-climbing-stairs": (
        "You are climbing a staircase. It takes n steps to reach the top.\n\n"
        "Each time you can climb either 1 or 2 steps. Given n, return how many "
        "distinct ways you can climb to the top."
    ),
    "lc-house-robber": (
        "You are a robber planning to rob houses along a street. Each house has a "
        "certain amount of money. Adjacent houses have security systems that will "
        "alert the police if both are robbed on the same night.\n\n"
        "Given nums where nums[i] is the money in the ith house, return the maximum "
        "amount you can rob without alerting the police."
    ),
    "lc-coin-change": (
        "Given an array coins of distinct coin denominations and an integer amount, "
        "return the fewest number of coins needed to make up that amount. If the "
        "amount cannot be made up, return -1.\n\n"
        "You may use each denomination as many times as you want."
    ),
    "lc-number-islands": (
        "Given an m x n 2D grid map of '1's (land) and '0's (water), return the "
        "number of islands.\n\n"
        "An island is surrounded by water and is formed by connecting adjacent "
        "lands horizontally or vertically."
    ),
    "lc-course-schedule": (
        "There are numCourses courses labeled from 0 to numCourses - 1. You are "
        "given prerequisites where [a, b] indicates you must take course b before "
        "course a.\n\n"
        "Return true if you can finish all courses, or false if there is a "
        "prerequisite cycle that makes completion impossible."
    ),
    "lc-merge-intervals": (
        "Given an array of intervals where intervals[i] = [start, end], merge all "
        "overlapping intervals and return an array of the non-overlapping intervals "
        "that cover all the intervals in the input.\n\n"
        "Two intervals overlap if the start of one is less than or equal to the "
        "end of the other."
    ),
}


PROBLEM_SOLUTIONS = {
    "lc-two-sum": "def two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        need = target - n\n        if need in seen:\n            return [seen[need], i]\n        seen[n] = i\n    return []",
    "lc-contains-duplicate": "def contains_duplicate(nums):\n    return len(set(nums)) != len(nums)",
    "lc-valid-anagram": "def is_anagram(s, t):\n    if len(s) != len(t):\n        return False\n    count = {}\n    for c in s:\n        count[c] = count.get(c, 0) + 1\n    for c in t:\n        if count.get(c, 0) == 0:\n            return False\n        count[c] -= 1\n    return True",
    "lc-best-time-stock": "def max_profit(prices):\n    best = 0\n    low = float('inf')\n    for p in prices:\n        low = min(low, p)\n        best = max(best, p - low)\n    return best",
    "lc-group-anagrams": "def group_anagrams(strs):\n    groups = {}\n    for s in strs:\n        key = tuple(sorted(s))\n        groups.setdefault(key, []).append(s)\n    return list(groups.values())",
    "lc-top-k-frequent": "def top_k_frequent(nums, k):\n    from collections import Counter\n    return [x for x, _ in Counter(nums).most_common(k)]",
    "lc-valid-palindrome": "def is_palindrome(s):\n    cleaned = [c.lower() for c in s if c.isalnum()]\n    return cleaned == cleaned[::-1]",
    "lc-two-sum-ii": "def two_sum_ii(numbers, target):\n    left, right = 0, len(numbers) - 1\n    while left < right:\n        s = numbers[left] + numbers[right]\n        if s == target:\n            return [left + 1, right + 1]\n        if s < target:\n            left += 1\n        else:\n            right -= 1\n    return []",
    "lc-3sum": "def three_sum(nums):\n    nums.sort()\n    out = []\n    for i in range(len(nums)):\n        if i > 0 and nums[i] == nums[i - 1]:\n            continue\n        left, right = i + 1, len(nums) - 1\n        while left < right:\n            s = nums[i] + nums[left] + nums[right]\n            if s == 0:\n                out.append([nums[i], nums[left], nums[right]])\n                left += 1\n                right -= 1\n                while left < right and nums[left] == nums[left - 1]:\n                    left += 1\n            elif s < 0:\n                left += 1\n            else:\n                right -= 1\n    return out",
    "lc-container-water": "def max_area(height):\n    left, right = 0, len(height) - 1\n    best = 0\n    while left < right:\n        best = max(best, min(height[left], height[right]) * (right - left))\n        if height[left] < height[right]:\n            left += 1\n        else:\n            right -= 1\n    return best",
    "lc-longest-substring": "def length_of_longest(s):\n    last = {}\n    left = best = 0\n    for right, ch in enumerate(s):\n        if ch in last and last[ch] >= left:\n            left = last[ch] + 1\n        last[ch] = right\n        best = max(best, right - left + 1)\n    return best",
    "lc-min-window-substring": "def min_window(s, t):\n    if not t:\n        return \"\"\n    need = {}\n    for c in t:\n        need[c] = need.get(c, 0) + 1\n    missing = len(t)\n    left = start = 0\n    best_len = 0\n    best = \"\"\n    for right, c in enumerate(s):\n        if c in need:\n            if need[c] > 0:\n                missing -= 1\n            need[c] -= 1\n        while missing == 0:\n            if best_len == 0 or right - left + 1 < best_len:\n                best_len = right - left + 1\n                start = left\n                best = s[left:right + 1]\n            left_c = s[left]\n            if left_c in need:\n                need[left_c] += 1\n                if need[left_c] > 0:\n                    missing += 1\n            left += 1\n    return best",
    "lc-valid-parentheses": "def is_valid_paren(s):\n    stack = []\n    pairs = {')': '(', '}': '{', ']': '['}\n    for c in s:\n        if c in pairs:\n            if not stack or stack[-1] != pairs[c]:\n                return False\n            stack.pop()\n        else:\n            stack.append(c)\n    return not stack",
    "lc-min-stack": "def min_stack_ops(ops):\n    stack = []\n    mins = []\n    out = []\n    for op in ops:\n        name = op[0]\n        if name == 'push':\n            v = op[1]\n            stack.append(v)\n            mins.append(v if not mins else min(v, mins[-1]))\n            out.append(None)\n        elif name == 'pop':\n            stack.pop()\n            mins.pop()\n            out.append(None)\n        elif name == 'top':\n            out.append(stack[-1])\n        elif name == 'getMin':\n            out.append(mins[-1])\n    return out",
    "lc-binary-search": "def binary_search(nums, target):\n    lo, hi = 0, len(nums) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if nums[mid] == target:\n            return mid\n        if nums[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1",
    "lc-search-rotated": "def search_rotated(nums, target):\n    lo, hi = 0, len(nums) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if nums[mid] == target:\n            return mid\n        if nums[lo] <= nums[mid]:\n            if nums[lo] <= target < nums[mid]:\n                hi = mid - 1\n            else:\n                lo = mid + 1\n        else:\n            if nums[mid] < target <= nums[hi]:\n                lo = mid + 1\n            else:\n                hi = mid - 1\n    return -1",
    "lc-reverse-linked-list": "def reverse_list(nums):\n    return list(reversed(nums))",
    "lc-merge-two-lists": "def merge_lists(a, b):\n    i = j = 0\n    out = []\n    while i < len(a) and j < len(b):\n        if a[i] <= b[j]:\n            out.append(a[i])\n            i += 1\n        else:\n            out.append(b[j])\n            j += 1\n    out.extend(a[i:])\n    out.extend(b[j:])\n    return out",
    "lc-linked-list-cycle": "def has_cycle(values, pos):\n    return pos >= 0",
    "lc-max-depth-tree": "def max_depth(nodes):\n    if not nodes:\n        return 0\n    def dfs(i):\n        if i >= len(nodes) or nodes[i] is None:\n            return 0\n        return 1 + max(dfs(2 * i + 1), dfs(2 * i + 2))\n    return dfs(0)",
    "lc-invert-tree": "def invert_tree(nodes):\n    if not nodes:\n        return nodes\n    def build(i):\n        if i >= len(nodes) or nodes[i] is None:\n            return None\n        return {'v': nodes[i], 'l': build(2 * i + 1), 'r': build(2 * i + 2)}\n    def invert(node):\n        if not node:\n            return None\n        node['l'], node['r'] = invert(node['r']), invert(node['l'])\n        return node\n    def serialize(node):\n        if not node:\n            return []\n        out = []\n        q = [node]\n        while q:\n            cur = q.pop(0)\n            if cur is None:\n                out.append(None)\n                continue\n            out.append(cur['v'])\n            q.append(cur.get('l'))\n            q.append(cur.get('r'))\n        while out and out[-1] is None:\n            out.pop()\n        return out\n    return serialize(invert(build(0)))",
    "lc-validate-bst": "def is_valid_bst(nodes):\n    if not nodes:\n        return True\n    def build(i):\n        if i >= len(nodes) or nodes[i] is None:\n            return None\n        return {'v': nodes[i], 'l': build(2 * i + 1), 'r': build(2 * i + 2)}\n    def valid(node, lo, hi):\n        if not node:\n            return True\n        v = node['v']\n        if v <= lo or v >= hi:\n            return False\n        return valid(node['l'], lo, v) and valid(node['r'], v, hi)\n    return valid(build(0), float('-inf'), float('inf'))",
    "lc-climbing-stairs": "def climb_stairs(n):\n    if n <= 2:\n        return n\n    a, b = 1, 2\n    for _ in range(3, n + 1):\n        a, b = b, a + b\n    return b",
    "lc-house-robber": "def rob(nums):\n    prev2 = prev1 = 0\n    for n in nums:\n        prev2, prev1 = prev1, max(prev1, prev2 + n)\n    return prev1",
    "lc-coin-change": "def coin_change(coins, amount):\n    dp = [10 ** 9] * (amount + 1)\n    dp[0] = 0\n    for a in range(1, amount + 1):\n        for c in coins:\n            if c <= a:\n                dp[a] = min(dp[a], dp[a - c] + 1)\n    return dp[amount] if dp[amount] != 10 ** 9 else -1",
    "lc-number-islands": "def num_islands(grid):\n    if not grid:\n        return 0\n    rows, cols = len(grid), len(grid[0])\n    count = 0\n    def dfs(r, c):\n        if r < 0 or c < 0 or r >= rows or c >= cols or grid[r][c] != '1':\n            return\n        grid[r][c] = '0'\n        dfs(r + 1, c)\n        dfs(r - 1, c)\n        dfs(r, c + 1)\n        dfs(r, c - 1)\n    for r in range(rows):\n        for c in range(cols):\n            if grid[r][c] == '1':\n                count += 1\n                dfs(r, c)\n    return count",
    "lc-course-schedule": "def can_finish(numCourses, prerequisites):\n    adj = [[] for _ in range(numCourses)]\n    for a, b in prerequisites:\n        adj[b].append(a)\n    state = [0] * numCourses\n    def dfs(u):\n        if state[u] == 1:\n            return False\n        if state[u] == 2:\n            return True\n        state[u] = 1\n        for v in adj[u]:\n            if not dfs(v):\n                return False\n        state[u] = 2\n        return True\n    return all(dfs(i) for i in range(numCourses))",
    "lc-merge-intervals": "def merge_intervals(intervals):\n    if not intervals:\n        return []\n    intervals.sort(key=lambda x: x[0])\n    merged = [intervals[0][:]]\n    for start, end in intervals[1:]:\n        if start <= merged[-1][1]:\n            merged[-1][1] = max(merged[-1][1], end)\n        else:\n            merged.append([start, end])\n    return merged",
}


def lc(
    pid: str,
    title: str,
    fn: str,
    desc: str,
    cases: list,
    starter1: str,
    *,
    topic: str,
    difficulty: str,
    global_order: int,
    leetcode_ref: int,
    hints: list[str] | None = None,
    approach: str = "",
    learning: list[str] | None = None,
    interview_questions: list[str] | None = None,
    solution_code: str = "",
):
    guide = TOPIC_GUIDES.get(topic, {})
    return {
        "id": pid,
        "title": title,
        "fn_name": fn,
        "description": desc,
        "topic": topic,
        "difficulty": difficulty,
        "global_order": global_order,
        "leetcode_ref": leetcode_ref,
        "track": "leetcodes",
        "test_cases": cases,
        "hints": hints or PROBLEM_HINTS.get(pid, []),
        "approach": approach or guide.get("approach", ""),
        "learning": learning or guide.get("learning", []),
        "interview_questions": interview_questions or guide.get("interview_questions", []),
        "solution_code": solution_code or PROBLEM_SOLUTIONS.get(pid, ""),
        "tiers": {
            1: {
                "starter_code": starter1,
                "explain_checklist": [
                    "Lee el enunciado y los ejemplos",
                    "Identifica entradas, salida y casos borde",
                    "Piensa en el patrón antes de escribir código",
                ],
                "hints_allowed": True,
            },
            2: {
                "starter_code": f"def {fn}(*args):\n    pass",
                "narration_prompts": [
                    "Explica tu enfoque en voz alta paso a paso",
                    "¿Cuál es la complejidad temporal y espacial?",
                    "¿Qué casos borde probaste?",
                ],
                "hints_allowed": True,
            },
            3: {
                "starter_code": f"def {fn}(*args):\n    pass",
                "narration_prompts": [],
                "hints_allowed": False,
            },
        },
    }


PROBLEMS = [
    lc("lc-two-sum", "Two Sum", "two_sum", DESCRIPTIONS_ES["lc-two-sum"],
       [{"args": [[2, 7, 11, 15], 9], "expected": [0, 1]}, {"args": [[3, 2, 4], 6], "expected": [1, 2]}],
       "def two_sum(nums, target):\n    # use a hash map\n    return []",
       topic="arrays_hashing", difficulty="easy", global_order=1, leetcode_ref=1),
    lc("lc-contains-duplicate", "Contains Duplicate", "contains_duplicate", DESCRIPTIONS_ES["lc-contains-duplicate"],
       [{"args": [[1, 2, 3, 1]], "expected": True}, {"args": [[1, 2, 3, 4]], "expected": False}],
       "def contains_duplicate(nums):\n    return False",
       topic="arrays_hashing", difficulty="easy", global_order=2, leetcode_ref=217),
    lc("lc-valid-anagram", "Valid Anagram", "is_anagram", DESCRIPTIONS_ES["lc-valid-anagram"],
       [{"args": ["anagram", "nagaram"], "expected": True}, {"args": ["rat", "car"], "expected": False}],
       "def is_anagram(s, t):\n    return False",
       topic="arrays_hashing", difficulty="easy", global_order=3, leetcode_ref=242),
    lc("lc-best-time-stock", "Best Time to Buy and Sell Stock", "max_profit",
       DESCRIPTIONS_ES["lc-best-time-stock"],
       [{"args": [[7, 1, 5, 3, 6, 4]], "expected": 5}, {"args": [[7, 6, 4, 3, 1]], "expected": 0}],
       "def max_profit(prices):\n    return 0",
       topic="arrays_hashing", difficulty="easy", global_order=4, leetcode_ref=121),
    lc("lc-group-anagrams", "Group Anagrams", "group_anagrams", DESCRIPTIONS_ES["lc-group-anagrams"],
       [{"args": [["eat", "tea", "tan", "ate", "nat", "bat"]],
         "expected": [["bat"], ["nat", "tan"], ["ate", "eat", "tea"]]}],
       "def group_anagrams(strs):\n    return []",
       topic="arrays_hashing", difficulty="medium", global_order=5, leetcode_ref=49),
    lc("lc-top-k-frequent", "Top K Frequent Elements", "top_k_frequent", DESCRIPTIONS_ES["lc-top-k-frequent"],
       [{"args": [[1, 1, 1, 2, 2, 3], 2], "expected": [1, 2]}, {"args": [[1], 1], "expected": [1]}],
       "def top_k_frequent(nums, k):\n    return []",
       topic="arrays_hashing", difficulty="medium", global_order=6, leetcode_ref=347),
    lc("lc-valid-palindrome", "Valid Palindrome", "is_palindrome", DESCRIPTIONS_ES["lc-valid-palindrome"],
       [{"args": ["A man, a plan, a canal: Panama"], "expected": True}, {"args": ["race a car"], "expected": False}],
       "def is_palindrome(s):\n    return False",
       topic="two_pointers", difficulty="easy", global_order=7, leetcode_ref=125),
    lc("lc-two-sum-ii", "Two Sum II", "two_sum_ii", DESCRIPTIONS_ES["lc-two-sum-ii"],
       [{"args": [[2, 7, 11, 15], 9], "expected": [1, 2]}, {"args": [[2, 3, 4], 6], "expected": [1, 3]}],
       "def two_sum_ii(numbers, target):\n    return []",
       topic="two_pointers", difficulty="medium", global_order=8, leetcode_ref=167),
    lc("lc-3sum", "3Sum", "three_sum", DESCRIPTIONS_ES["lc-3sum"],
       [{"args": [[-1, 0, 1, 2, -1, -4]], "expected": [[-1, -1, 2], [-1, 0, 1]]},
        {"args": [[0, 1, 1]], "expected": []}],
       "def three_sum(nums):\n    return []",
       topic="two_pointers", difficulty="medium", global_order=9, leetcode_ref=15),
    lc("lc-container-water", "Container With Most Water", "max_area", DESCRIPTIONS_ES["lc-container-water"],
       [{"args": [[1, 8, 6, 2, 5, 4, 8, 3, 7]], "expected": 49}, {"args": [[1, 1]], "expected": 1}],
       "def max_area(height):\n    return 0",
       topic="two_pointers", difficulty="medium", global_order=10, leetcode_ref=11),
    lc("lc-longest-substring", "Longest Substring Without Repeating", "length_of_longest",
       DESCRIPTIONS_ES["lc-longest-substring"],
       [{"args": ["abcabcbb"], "expected": 3}, {"args": ["bbbbb"], "expected": 1}, {"args": ["pwwkew"], "expected": 3}],
       "def length_of_longest(s):\n    return 0",
       topic="sliding_window", difficulty="medium", global_order=11, leetcode_ref=3),
    lc("lc-min-window-substring", "Minimum Window Substring", "min_window",
       DESCRIPTIONS_ES["lc-min-window-substring"],
       [{"args": ["ADOBECODEBANC", "ABC"], "expected": "BANC"}, {"args": ["a", "a"], "expected": "a"}],
       "def min_window(s, t):\n    return \"\"",
       topic="sliding_window", difficulty="hard", global_order=12, leetcode_ref=76),
    lc("lc-valid-parentheses", "Valid Parentheses", "is_valid_paren", DESCRIPTIONS_ES["lc-valid-parentheses"],
       [{"args": ["()"], "expected": True}, {"args": ["()[]{}"], "expected": True}, {"args": ["(]"], "expected": False}],
       "def is_valid_paren(s):\n    return False",
       topic="stack", difficulty="easy", global_order=13, leetcode_ref=20),
    lc("lc-binary-search", "Binary Search", "binary_search", DESCRIPTIONS_ES["lc-binary-search"],
       [{"args": [[-1, 0, 3, 5, 9, 12], 9], "expected": 4}, {"args": [[-1, 0, 3, 5, 9, 12], 2], "expected": -1}],
       "def binary_search(nums, target):\n    return -1",
       topic="binary_search", difficulty="easy", global_order=15, leetcode_ref=704),
    lc("lc-search-rotated", "Search in Rotated Sorted Array", "search_rotated",
       DESCRIPTIONS_ES["lc-search-rotated"],
       [{"args": [[4, 5, 6, 7, 0, 1, 2], 0], "expected": 4}, {"args": [[4, 5, 6, 7, 0, 1, 2], 3], "expected": -1}],
       "def search_rotated(nums, target):\n    return -1",
       topic="binary_search", difficulty="medium", global_order=16, leetcode_ref=33),
    lc("lc-reverse-linked-list", "Reverse Linked List", "reverse_list",
       DESCRIPTIONS_ES["lc-reverse-linked-list"],
       [{"args": [[1, 2, 3, 4, 5]], "expected": [5, 4, 3, 2, 1]}, {"args": [[1, 2]], "expected": [2, 1]}],
       "def reverse_list(nums):\n    return nums",
       topic="linked_list", difficulty="easy", global_order=17, leetcode_ref=206),
    lc("lc-merge-two-lists", "Merge Two Sorted Lists", "merge_lists",
       DESCRIPTIONS_ES["lc-merge-two-lists"],
       [{"args": [[1, 2, 4], [1, 3, 4]], "expected": [1, 1, 2, 3, 4, 4]}, {"args": [[], []], "expected": []}],
       "def merge_lists(a, b):\n    return []",
       topic="linked_list", difficulty="easy", global_order=18, leetcode_ref=21),
    lc("lc-linked-list-cycle", "Linked List Cycle", "has_cycle",
       DESCRIPTIONS_ES["lc-linked-list-cycle"],
       [{"args": [[3, 2, 0, -4], 1], "expected": True}, {"args": [[1, 2], 0], "expected": True}, {"args": [[1], -1], "expected": False}],
       "def has_cycle(values, pos):\n    return pos >= 0",
       topic="linked_list", difficulty="easy", global_order=19, leetcode_ref=141),
    lc("lc-max-depth-tree", "Maximum Depth of Binary Tree", "max_depth",
       DESCRIPTIONS_ES["lc-max-depth-tree"],
       [{"args": [[3, 9, 20, None, None, 15, 7]], "expected": 3},
        {"args": [[1, None, 2]], "expected": 2}],
       "def max_depth(nodes):\n    return 0",
       topic="trees", difficulty="easy", global_order=20, leetcode_ref=104),
    lc("lc-invert-tree", "Invert Binary Tree", "invert_tree",
       DESCRIPTIONS_ES["lc-invert-tree"],
       [{"args": [[4, 2, 7, 1, 3, 6, 9]], "expected": [4, 7, 2, 9, 6, 3, 1]}],
       "def invert_tree(nodes):\n    return nodes",
       topic="trees", difficulty="easy", global_order=21, leetcode_ref=226),
    lc("lc-validate-bst", "Validate BST", "is_valid_bst",
       DESCRIPTIONS_ES["lc-validate-bst"],
       [{"args": [[2, 1, 3]], "expected": True},
        {"args": [[5, 1, 4, None, None, 3, 6]], "expected": False}],
       "def is_valid_bst(nodes):\n    return False",
       topic="trees", difficulty="medium", global_order=22, leetcode_ref=98),
    lc("lc-climbing-stairs", "Climbing Stairs", "climb_stairs", DESCRIPTIONS_ES["lc-climbing-stairs"],
       [{"args": [2], "expected": 2}, {"args": [3], "expected": 3}, {"args": [5], "expected": 8}],
       "def climb_stairs(n):\n    return 0",
       topic="dp_1d", difficulty="easy", global_order=23, leetcode_ref=70),
    lc("lc-house-robber", "House Robber", "rob", DESCRIPTIONS_ES["lc-house-robber"],
       [{"args": [[1, 2, 3, 1]], "expected": 4}, {"args": [[2, 7, 9, 3, 1]], "expected": 12}],
       "def rob(nums):\n    return 0",
       topic="dp_1d", difficulty="medium", global_order=24, leetcode_ref=198),
    lc("lc-coin-change", "Coin Change", "coin_change", DESCRIPTIONS_ES["lc-coin-change"],
       [{"args": [[1, 2, 5], 11], "expected": 3}, {"args": [[2], 3], "expected": -1}],
       "def coin_change(coins, amount):\n    return -1",
       topic="dp_1d", difficulty="medium", global_order=25, leetcode_ref=322),
    lc("lc-number-islands", "Number of Islands", "num_islands", DESCRIPTIONS_ES["lc-number-islands"],
       [{"args": [[["1", "1", "1", "1", "0"], ["1", "1", "0", "1", "0"], ["1", "1", "0", "0", "0"], ["0", "0", "0", "0", "0"]]], "expected": 1},
        {"args": [[["1", "1", "0", "0", "0"], ["1", "1", "0", "0", "0"], ["0", "0", "1", "0", "0"], ["0", "0", "0", "1", "1"]]], "expected": 3}],
       "def num_islands(grid):\n    return 0",
       topic="graphs", difficulty="medium", global_order=26, leetcode_ref=200),
    lc("lc-course-schedule", "Course Schedule", "can_finish",
       DESCRIPTIONS_ES["lc-course-schedule"],
       [{"args": [2, [[1, 0]]], "expected": True}, {"args": [2, [[1, 0], [0, 1]]], "expected": False}],
       "def can_finish(numCourses, prerequisites):\n    return False",
       topic="graphs", difficulty="medium", global_order=27, leetcode_ref=207),
    lc("lc-merge-intervals", "Merge Intervals", "merge_intervals", DESCRIPTIONS_ES["lc-merge-intervals"],
       [{"args": [[[1, 3], [2, 6], [8, 10], [15, 18]]], "expected": [[1, 6], [8, 10], [15, 18]]},
        {"args": [[[1, 4], [4, 5]]], "expected": [[1, 5]]}],
       "def merge_intervals(intervals):\n    return []",
       topic="intervals", difficulty="medium", global_order=28, leetcode_ref=56),
]

PROBLEMS.insert(14, lc(
    "lc-min-stack", "Min Stack", "min_stack_ops",
    DESCRIPTIONS_ES["lc-min-stack"],
    [{"args": [[["push", -2], ["push", 0], ["push", -3], ["getMin"], ["pop"], ["top"], ["getMin"]]],
      "expected": [None, None, None, -3, None, 0, -2]}],
    "def min_stack_ops(ops):\n    stack = []\n    mins = []\n    out = []\n    for op in ops:\n        name = op[0]\n        if name == 'push':\n            v = op[1]\n            stack.append(v)\n            # update mins\n        elif name == 'pop':\n            pass\n        elif name == 'top':\n            out.append(stack[-1])\n        elif name == 'getMin':\n            out.append(___)\n    return out",
    topic="stack", difficulty="medium", global_order=14, leetcode_ref=155,
))
# Re-number global_order after insert
for i, p in enumerate(PROBLEMS):
    p["global_order"] = i + 1


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def validate_solutions(problems: list[dict]) -> None:
    import sys
    sys.path.insert(0, str(ROOT / "backend"))
    from app.executor import run_leetcode_code

    failed = []
    for p in problems:
        sol = p.get("solution_code", "")
        if not sol:
            failed.append((p["id"], "missing solution_code"))
            continue
        res = run_leetcode_code(sol, p["test_cases"], p["fn_name"])
        if not res.get("passed"):
            failed.append((p["id"], res.get("error") or res.get("results")))
    if failed:
        for pid, err in failed:
            print(f"Solution check failed for {pid}: {err}")
        raise SystemExit(1)


def main() -> None:
    validate_solutions(PROBLEMS)
    OUT.mkdir(parents=True, exist_ok=True)
    topics: dict[str, list[str]] = {}
    for p in PROBLEMS:
        write_yaml(OUT / f"{p['id']}.yaml", p)
        topics.setdefault(p["topic"], []).append(p["id"])

    topic_titles = {
        "arrays_hashing": "Arrays & Hashing",
        "two_pointers": "Two Pointers",
        "sliding_window": "Sliding Window",
        "stack": "Stack",
        "binary_search": "Binary Search",
        "linked_list": "Linked List",
        "trees": "Trees",
        "dp_1d": "1D Dynamic Programming",
        "graphs": "Graphs",
        "intervals": "Intervals",
    }

    schedule = {
        "track": "leetcodes",
        "topics": [
            {"id": tid, "title": topic_titles[tid], "problems": topics[tid]}
            for tid in topic_titles
            if tid in topics
        ],
        "orientador": {
            "minutes_per_tier_attempt": 50,
            "minutes_per_problem_base": 10,
            "steps_per_problem": 1,
            "max_problems_per_session": 1,
            "min_minutes": 30,
            "max_minutes": 90,
            "default_minutes": 60,
            "minute_presets": [45, 60, 90],
            "focus_topics": ["arrays_hashing", "two_pointers"],
            "skip_hard_until_focus_done": True,
            "hint_lock_minutes": 25,
            "repaso_days": 7,
        },
    }
    SCHEDULE.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(SCHEDULE, schedule)
    print(f"Generated {len(PROBLEMS)} problems in {OUT}")
    print(f"Schedule: {SCHEDULE}")


if __name__ == "__main__":
    main()
