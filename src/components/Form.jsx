import React, { useEffect, useState } from 'react';
import { AutoComplete } from "primereact/autocomplete";
import axios from 'axios';
import { IoIosSend } from "react-icons/io";
import '../style/Button.css'
import '../style/Form.css'
export default function Form() {
    const [prompts, setPrompts] = useState([]);
    const [selectedPrompt, setSelectedPrompt] = useState('');
    const [filteredPrompts, setFilteredPrompts] = useState([]);
    const [response, setResponse] = useState(''); // To display the API response

    const host = process.env.REACT_APP_API_HOST                   
    const port = process.env.REACT_APP_API_PORT                   

    // Sample prompt questions
    const samplePrompts = [
        "Apa prosedur untuk mengajukan cuti?",
        "Berapa sisa cuti yang saya miliki?",
        "Bagaimana prosedur untuk membuat surat dinas?",
        "Apa langkah-langkah untuk mengajukan training atau sertifikasi?",
        "Bagaimana cara mengajukan penambahan karyawan?",
        "Mengapa jaringan saya tidak bisa terhubung ke wifi A?",
        "Bagaimana cara mereset password email saya?",
        "Apa langkah-langkah untuk mengaktifkan VPN?",
        "Bagaimana cara menggunakan printer di kantor?",
        "Apa prosedur untuk mengajukan pengadaan laptop baru?",
        "Bagaimana cara mengakses laporan keuangan?",
        "Apa langkah-langkah untuk mendapatkan slip gaji?",
        "Bagaimana cara mengajukan reimburse?",
        "Apa prosedur untuk mengajukan penggantian kartu kredit?",
        "Bagaimana cara mengajukan uang dinas?"
      ];

    const search = (event) => {
        setTimeout(() => {
            let _filteredPrompts;

            if (!event.query.trim().length) {
                _filteredPrompts = [...prompts];
            } else {
                _filteredPrompts = prompts.filter((prompt) => {
                    return prompt.toLowerCase().startsWith(event.query.toLowerCase());
                });
            }

            setFilteredPrompts(_filteredPrompts);
        }, 250);
    };

    const fetchResponse = async (prompt) => {
        try {
            const response = await axios.post(`${host}:${port}/ask`, { question: prompt });
            setResponse(response.data.response); // Update the response state
        } catch (error) {
            console.error("Error fetching API response:", error);
            setResponse('Maaf, terjadi kesalahan saat menghubungi server.');
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault(); // Prevent default form submission
        if (selectedPrompt.trim() === '') {
            alert("Please select or type a prompt before submitting.");
            return;
        }
        fetchResponse(selectedPrompt);
        setSelectedPrompt('') // Call API with the selected prompt
    };

    useEffect(() => {
        setPrompts(samplePrompts); // Set sample prompts
    }, []);

    return (
        <div >
            <form onSubmit={handleSubmit}>
                <div className='formInput p-fluid'>
                    <AutoComplete
                        
                        value={selectedPrompt} 
                        suggestions={filteredPrompts} 
                        completeMethod={search} 
                        onChange={(e) => setSelectedPrompt(e.value)} 
                        placeholder="Ask a question..."

                    />

                </div>
                <div className="buttonInput">
                    <button 
                        type="submit" 
                        className="sendButton" 
                        >
                        <IoIosSend />
                    </button>
                </div>
            </form>

        </div>
    );
}
