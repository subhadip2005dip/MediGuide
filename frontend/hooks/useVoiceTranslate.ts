export async function recordAndTranslate({
  speaker,
  patientLang,
  doctorLang,
  API_URL,
  onResult,
  speak,
}: any) {
  let stream: MediaStream | null = null;

  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    const recorder = new MediaRecorder(stream);
    const chunks: Blob[] = [];

    return new Promise((resolve, reject) => {
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      recorder.onstop = async () => {
        try {
          stream?.getTracks().forEach((t) => t.stop());

          const blob = new Blob(chunks, { type: "audio/webm" });
          if (blob.size === 0) {
            throw new Error("No audio recorded");
          }

          const sourceLang = speaker === "patient" ? patientLang : doctorLang;
          const targetLang = speaker === "patient" ? doctorLang : patientLang;

          const formData = new FormData();
          formData.append("audio", blob);
          formData.append("sourceLang", sourceLang);
          formData.append("targetLang", targetLang);

          const res = await fetch(`${API_URL}/translate/audio`, {
            method: "POST",
            body: formData,
          });

          if (!res.ok) {
            throw new Error(`API error: ${res.status} ${res.statusText}`);
          }

          const data = await res.json();

          if (data.error) {
            throw new Error(`API returned error: ${data.error}`);
          }

          // Validate response structure
          if (!data.original_text || !data.translated_text || !data.tts_lang) {
            console.error("Invalid API response structure:", data);
            throw new Error("Invalid response from translation API");
          }

          const result = {
            id: crypto.randomUUID(),
            speaker,
            original: data.original_text,
            translated: data.translated_text,
            tts_lang: data.tts_lang,
            time: new Date().toLocaleTimeString(),
          };

          onResult(result);
          speak(data.translated_text, data.tts_lang);
          resolve(result);
        } catch (err) {
          reject(err);
        }
      };

      recorder.onerror = (event) => {
        stream?.getTracks().forEach((t) => t.stop());
        reject(new Error(`Recorder error: ${event.error}`));
      };

      recorder.start();
      setTimeout(() => recorder.stop(), 5000);
    });
  } catch (err) {
    stream?.getTracks().forEach((t) => t.stop());
    throw err;
  }
}
